import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const [clientId] = useState(() => 
    'player_' + Math.random().toString(36).substr(2, 9)
  )
  
  const [gameMode, setGameMode] = useState(null)
  const [gameId, setGameId] = useState(null)
  const [gameStatus, setGameStatus] = useState('menu')
  
  const [inputWord, setInputWord] = useState('')
  const [guessHistory, setGuessHistory] = useState([])
  const [attempts, setAttempts] = useState(0)
  const [message, setMessage] = useState('')
  const [targetWord, setTargetWord] = useState('')
  
  const [opponentId, setOpponentId] = useState(null)
  const [opponentAttempts, setOpponentAttempts] = useState(0)
  const [opponentLastWord, setOpponentLastWord] = useState('')
  
  const ws = useRef(null)

  useEffect(() => {
    console.log('🔌 Подключение к серверу...')
    ws.current = new WebSocket(`ws://localhost:8000/ws/${clientId}`)
    
    ws.current.onopen = () => {
      console.log('✓ Соединение установлено')
    }
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('📨 Получено:', data)
      
      if (data.type === 'game_started') {
        setGameId(data.game_id)
        setGameMode(data.mode)
        setGameStatus('playing')
        setGuessHistory([])
        setAttempts(0)
        setOpponentAttempts(0)
        
        if (data.mode === 'solo') {
          setMessage('🎮 Игра началась! Угадайте слово.')
        } else {
          setOpponentId(data.opponent)
          setMessage('⚔️ Соперник найден! Кто быстрее угадает слово.')
        }
      }
      
      else if (data.type === 'waiting_for_opponent') {
        setGameStatus('waiting')
        setMessage('⏳ Поиск соперника...')
      }
      
      else if (data.type === 'guess_result') {
        setGuessHistory(data.history)
        setAttempts(data.attempts)
        
        if (data.is_correct) {
          setGameStatus('finished')
          setTargetWord(data.word)
          setMessage(`🎉 Победа! Вы угадали слово "${data.word}" за ${data.attempts} попыток!`)
        } else {
          const rankText = data.rank < 100 ? `очень близко (ранг ${data.rank})` :
                          data.rank < 500 ? `близко (ранг ${data.rank})` :
                          `далеко (ранг ${data.rank})`
          setMessage(`"${data.word}" - ${rankText}`)
        }
      }
      
      else if (data.type === 'opponent_guess') {
        setOpponentAttempts(data.attempts)
        setOpponentLastWord(data.last_word || '')
      }
      
      else if (data.type === 'game_over') {
        setGameStatus('finished')
        setTargetWord(data.word)
        if (data.winner === clientId) {
          setMessage(`🎉 Победа! Слово: "${data.word}"`)
        } else {
          setMessage(`😔 Соперник победил. Слово было: "${data.word}"`)
        }
      }
      
      else if (data.type === 'error') {
        setMessage('❌ ' + data.message)
      }
    }
    
    ws.current.onerror = (error) => {
      console.error('❌ Ошибка WebSocket:', error)
      setMessage('❌ Ошибка подключения к серверу')
    }
    
    ws.current.onclose = () => {
      console.log('🔌 Соединение закрыто')
    }

    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [clientId])

  const startGame = (mode) => {
    console.log(`🎮 Начинаем игру в режиме: ${mode}`)
    ws.current.send(JSON.stringify({
      action: mode === 'solo' ? 'start_solo' : 'start_multiplayer'
    }))
  }

  const makeGuess = () => {
    const word = inputWord.trim()
    
    if (!word) {
      setMessage('⚠️ Введите слово')
      return
    }
    
    const russianLetters = /^[а-яёА-ЯЁ]+$/
    if (!russianLetters.test(word)) {
      setMessage('❌ Пожалуйста, вводите только русские слова')
      setInputWord('')
      return
    }
    
    console.log(`📤 Отправляем попытку: ${word}`)
    ws.current.send(JSON.stringify({
      action: 'guess',
      game_id: gameId,
      word: word
    }))
    
    setInputWord('')
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      makeGuess()
    }
  }

  const resetGame = () => {
    setGameStatus('menu')
    setGameMode(null)
    setGameId(null)
    setMessage('')
    setGuessHistory([])
    setAttempts(0)
    setOpponentAttempts(0)
    setTargetWord('')
    setInputWord('')
  }

  const getRankColor = (rank) => {
    if (rank <= 10) return '#27ae60'
    if (rank <= 50) return '#f39c12'
    if (rank <= 200) return '#e67e22'
    return '#e74c3c'
  }

  return (
    <div className="App">
      <header>
        <h1>🎯 Игра в Слова</h1>
        <p className="subtitle">Угадайте загаданное слово по семантической близости</p>
      </header>

      {gameStatus === 'menu' && (
        <div className="menu">
          <h2>Выберите режим игры</h2>
          <div className="menu-buttons">
            <button onClick={() => startGame('solo')} className="btn btn-primary">
              <span className="btn-icon">🎮</span>
              <span className="btn-text">
                <strong>Соло режим</strong>
                <small>Играйте в своем темпе</small>
              </span>
            </button>
            <button onClick={() => startGame('multiplayer')} className="btn btn-secondary">
              <span className="btn-icon">⚔️</span>
              <span className="btn-text">
                <strong>С соперником</strong>
                <small>Кто быстрее угадает</small>
              </span>
            </button>
          </div>
          
          <div className="rules">
            <h3>📖 Как играть:</h3>
            <ul>
              <li>Введите любое существительное - система покажет насколько оно близко к загаданному</li>
              <li>Чем меньше ранг (число), тем ближе к ответу</li>
              <li>Используйте подсказки из истории попыток</li>
              <li>Побеждает тот, кто угадает слово первым!</li>
              <li>Вводите только существительные (названия предметов, животных, явлений)</li>
            </ul>
          </div>
        </div>
      )}

      {gameStatus === 'waiting' && (
        <div className="waiting">
          <div className="spinner"></div>
          <h2>{message}</h2>
          <button onClick={resetGame} className="btn btn-outline">
            Отмена
          </button>
        </div>
      )}

      {gameStatus === 'playing' && (
        <div className="game">
          <div className="message-bar">
            {message}
          </div>

          <div className="stats">
            <div className="stat-card">
              <div className="stat-label">Ваши попытки</div>
              <div className="stat-value">{attempts}</div>
            </div>
            
            {gameMode === 'multiplayer' && (
              <div className="stat-card opponent">
                <div className="stat-label">Попытки соперника</div>
                <div className="stat-value">{opponentAttempts}</div>
                {opponentLastWord && (
                  <div className="stat-hint">последнее: {opponentLastWord}</div>
                )}
              </div>
            )}
          </div>

          <div className="input-area">
            <input
              type="text"
              value={inputWord}
              onChange={(e) => setInputWord(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Введите существительное..."
              autoFocus
              className="word-input"
            />
            <button onClick={makeGuess} className="btn btn-primary">
              Проверить
            </button>
          </div>

          {guessHistory.length > 0 && (
            <div className="history">
              <h3>📝 История попыток (отсортировано по близости):</h3>
              <div className="history-list">
                {guessHistory.map((guess, idx) => (
                  <div key={idx} className="guess-item">
                    <div className="guess-rank" style={{color: getRankColor(guess.rank)}}>
                      #{guess.rank}
                    </div>
                    <div className="guess-word">{guess.word}</div>
                    <div className="guess-similarity">
                      <div className="similarity-bar">
                        <div 
                          className="similarity-fill"
                          style={{
                            width: `${guess.similarity * 100}%`,
                            backgroundColor: getRankColor(guess.rank)
                          }}
                        ></div>
                      </div>
                      <span className="similarity-value">
                        {(guess.similarity * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {gameStatus === 'finished' && (
        <div className="finished">
          <div className="result-message">
            <h2>{message}</h2>
            {targetWord && (
              <div className="target-word">
                Загаданное слово: <strong>{targetWord}</strong>
              </div>
            )}
          </div>
          
          <div className="final-stats">
            <div className="final-stat">
              <div className="final-stat-label">Всего попыток</div>
              <div className="final-stat-value">{attempts}</div>
            </div>
          </div>

          <button onClick={resetGame} className="btn btn-primary btn-large">
            🎮 Играть снова
          </button>
        </div>
      )}
    </div>
  )
}

export default App
