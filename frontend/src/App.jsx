import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const [clientId] = useState(() => 'player_' + Math.random().toString(36).substr(2, 9))
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
  
  const [showRules, setShowRules] = useState(false)
  const [showStats, setShowStats] = useState(false)
  
  // Таймер времени на сайте
  const [totalTimeSpent, setTotalTimeSpent] = useState(() => {
    const saved = localStorage.getItem('wordweave_total_time')
    return saved ? parseInt(saved) : 0
  })
  
  const [stats, setStats] = useState(() => {
    const saved = localStorage.getItem('wordweave_stats')
    return saved ? JSON.parse(saved) : {
      totalGames: 0,
      totalWins: 0,
      totalAttempts: 0,
      bestScore: null,
      totalPlayTime: 0
    }
  })
  
  const ws = useRef(null)
  const sessionStartTime = useRef(Date.now())
  const timeInterval = useRef(null)

  // Таймер времени на сайте
  useEffect(() => {
    timeInterval.current = setInterval(() => {
      const newTime = totalTimeSpent + 1
      setTotalTimeSpent(newTime)
      localStorage.setItem('wordweave_total_time', newTime.toString())
    }, 1000) // Каждую секунду
    
    return () => {
      if (timeInterval.current) {
        clearInterval(timeInterval.current)
      }
    }
  }, [totalTimeSpent])

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
        sessionStartTime.current = Date.now()
        
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
        if (data.error) {
          setMessage('❌ ' + data.error)
          return
        }
        
        setGuessHistory(data.history || [])
        setAttempts(data.attempts || attempts)
        
        if (data.is_correct) {
          setGameStatus('finished')
          setTargetWord(data.target_word)
          const gameTime = Math.floor((Date.now() - sessionStartTime.current) / 1000)
          setMessage(`🎉 Победа! Вы угадали слово "${data.target_word}" за ${data.attempts} попыток!`)
          updateStatsFunc(true, data.attempts, gameTime)
        } else {
          const rankText = data.rank < 100 ? `очень близко (ранг ${data.rank})` :
                          data.rank < 500 ? `близко (ранг ${data.rank})` :
                          data.rank < 1000 ? `средне (ранг ${data.rank})` :
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
        const gameTime = Math.floor((Date.now() - sessionStartTime.current) / 1000)
        
        if (data.winner === clientId) {
          setMessage(`🎉 Победа! Слово: "${data.word}"`)
          updateStatsFunc(true, attempts, gameTime)
        } else {
          setMessage(`😔 Соперник победил. Слово было: "${data.word}"`)
          updateStatsFunc(false, attempts, gameTime)
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

  const updateStatsFunc = (isWin, attemptCount, gameTime) => {
    console.log('📊 Обновление статистики:', { isWin, attemptCount, gameTime })
    
    const newStats = {
      totalGames: stats.totalGames + 1,
      totalWins: isWin ? stats.totalWins + 1 : stats.totalWins,
      totalAttempts: stats.totalAttempts + attemptCount,
      totalPlayTime: stats.totalPlayTime + gameTime,
      bestScore: !stats.bestScore || (isWin && attemptCount < stats.bestScore) 
        ? attemptCount 
        : stats.bestScore
    }
    
    console.log('✓ Новая статистика:', newStats)
    setStats(newStats)
    localStorage.setItem('wordweave_stats', JSON.stringify(newStats))
  }

  const startGame = (mode) => {
    console.log(`🎮 Начинаем игру в режиме: ${mode}`)
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        action: mode === 'solo' ? 'start_solo' : 'start_multiplayer'
      }))
    }
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
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        action: 'guess',
        game_id: gameId,
        word: word
      }))
    }
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

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}ч ${minutes}м`
    } else if (minutes > 0) {
      return `${minutes}м ${secs}с`
    } else {
      return `${secs}с`
    }
  }

  return (
    <div className="App">
      <header>
        <h1>🎮 WORDWEAVE</h1>
        <p className="subtitle">Угадай слово через семантические ассоциации</p>
        
        <div className="header-buttons">
          <button className="btn btn-outline btn-small" onClick={() => setShowRules(true)}>
            📖 Правила
          </button>
          <button className="btn btn-outline btn-small" onClick={() => setShowStats(true)}>
            📊 Статистика
          </button>
        </div>
      </header>

      {gameStatus === 'menu' && (
        <div className="menu">
          <h2>Выберите режим игры</h2>
          <div className="menu-buttons">
            <button className="btn btn-primary" onClick={() => startGame('solo')}>
              <div className="btn-icon">👤</div>
              <div className="btn-text">
                <strong>Одиночная игра</strong>
                <small>Играйте в своем темпе</small>
              </div>
            </button>
            <button className="btn btn-primary" onClick={() => startGame('multiplayer')}>
              <div className="btn-icon">⚔️</div>
              <div className="btn-text">
                <strong>Мультиплеер</strong>
                <small>Соревнуйтесь с другими</small>
              </div>
            </button>
          </div>
        </div>
      )}

      {gameStatus === 'waiting' && (
        <div className="waiting">
          <div className="spinner"></div>
          <h2>Поиск соперника...</h2>
          <p>Ожидайте подключения другого игрока</p>
          <button className="btn btn-secondary" onClick={resetGame}>
            Отмена
          </button>
        </div>
      )}

      {gameStatus === 'playing' && (
        <div className="game">
          <div className="message-bar">{message}</div>
          
          <div className="stats">
            <div className="stat-card">
              <div className="stat-label">Ваши попытки</div>
              <div className="stat-value">{attempts}</div>
              <div className="stat-hint">Продолжайте!</div>
            </div>
            
            {gameMode === 'multiplayer' && (
              <div className="stat-card opponent">
                <div className="stat-label">Соперник</div>
                <div className="stat-value">{opponentAttempts}</div>
                <div className="stat-hint">
                  {opponentLastWord ? `Последнее: ${opponentLastWord}` : 'Думает...'}
                </div>
              </div>
            )}
          </div>

          <div className="input-area">
            <input
              type="text"
              className="word-input"
              value={inputWord}
              onChange={(e) => setInputWord(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Введите слово..."
              autoFocus
            />
            <button className="btn btn-primary btn-large" onClick={makeGuess}>
              Проверить →
            </button>
          </div>

          <div className="history">
            <h3>История попыток (сортировано по близости)</h3>
            <div className="history-list">
              {guessHistory.length === 0 ? (
                <p style={{textAlign: 'center', color: '#999', padding: '20px'}}>
                  Ваши попытки появятся здесь
                </p>
              ) : (
                guessHistory.map((guess, index) => (
                  <div key={index} className="guess-item">
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
                            background: `linear-gradient(90deg, ${getRankColor(guess.rank)}, ${getRankColor(guess.rank)}99)`
                          }}
                        ></div>
                      </div>
                      <div className="similarity-value">
                        {(guess.similarity * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
          
          <button className="btn btn-secondary" onClick={resetGame} style={{marginTop: '20px'}}>
            Вернуться в меню
          </button>
        </div>
      )}

      {gameStatus === 'finished' && (
        <div className="finished">
          <div className="result-message">
            <h2>{message.includes('Победа') ? '🎉 Поздравляем!' : '😔 Игра окончена'}</h2>
          </div>
          <div className="target-word">
            Загаданное слово: <strong>{targetWord}</strong>
          </div>
          <div className="final-stats">
            <div className="final-stat">
              <div className="final-stat-label">Попыток</div>
              <div className="final-stat-value">{attempts}</div>
            </div>
            <div className="final-stat">
              <div className="final-stat-label">Слов проверено</div>
              <div className="final-stat-value">{guessHistory.length}</div>
            </div>
          </div>
          <button className="btn btn-primary btn-large" onClick={resetGame}>
            Играть снова
          </button>
        </div>
      )}

      {showRules && (
        <div className="modal" onClick={() => setShowRules(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📖 Правила игры</h2>
              <button className="modal-close" onClick={() => setShowRules(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="rule-item">
                <div className="rule-number">1</div>
                <div className="rule-text">
                  <h4>Цель игры</h4>
                  <p>Угадайте загаданное слово через семантические ассоциации</p>
                </div>
              </div>
              <div className="rule-item">
                <div className="rule-number">2</div>
                <div className="rule-text">
                  <h4>Как играть</h4>
                  <p>Вводите слова, и система покажет насколько они близки к загаданному</p>
                </div>
              </div>
              <div className="rule-item">
                <div className="rule-number">3</div>
                <div className="rule-text">
                  <h4>Ранг близости</h4>
                  <p>Чем меньше ранг — тем ближе слово. Ранг 1-10 означает очень близкое слово!</p>
                </div>
              </div>
              <div className="rule-item">
                <div className="rule-number">4</div>
                <div className="rule-text">
                  <h4>База слов</h4>
                  <p>В игре 450,000+ русских существительных из проверенных словарей</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {showStats && (
        <div className="modal" onClick={() => setShowStats(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📊 Статистика</h2>
              <button className="modal-close" onClick={() => setShowStats(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="stats-grid">
                <div className="stat-card-modal">
                  <div className="stat-icon">🎯</div>
                  <div className="stat-value">{stats.totalGames}</div>
                  <div className="stat-label">Всего игр</div>
                </div>
                <div className="stat-card-modal">
                  <div className="stat-icon">🏆</div>
                  <div className="stat-value">{stats.totalWins}</div>
                  <div className="stat-label">Побед</div>
                </div>
                <div className="stat-card-modal">
                  <div className="stat-icon">📈</div>
                  <div className="stat-value">
                    {stats.totalGames > 0 ? Math.round(stats.totalAttempts / stats.totalGames) : 0}
                  </div>
                  <div className="stat-label">Средних попыток</div>
                </div>
                <div className="stat-card-modal">
                  <div className="stat-icon">⚡</div>
                  <div className="stat-value">{stats.bestScore || '-'}</div>
                  <div className="stat-label">Лучший результат</div>
                </div>
              </div>

              {/* НОВАЯ СЕКЦИЯ: Время на сайте */}
              <div className="time-section">
                <h3>⏱️ Время на сайте</h3>
                <div className="time-display">
                  <div className="time-value">{formatTime(totalTimeSpent)}</div>
                  <div className="time-label">Всего времени</div>
                </div>
                {stats.totalPlayTime > 0 && (
                  <div className="time-display">
                    <div className="time-value">{formatTime(stats.totalPlayTime)}</div>
                    <div className="time-label">Время в играх</div>
                  </div>
                )}
              </div>

              <div className="win-rate">
                <h3>Процент побед</h3>
                <div className="win-rate-bar">
                  <div 
                    className="win-rate-fill" 
                    style={{
                      width: `${stats.totalGames > 0 ? (stats.totalWins / stats.totalGames * 100) : 0}%`
                    }}
                  ></div>
                </div>
                <p>{stats.totalGames > 0 ? ((stats.totalWins / stats.totalGames * 100).toFixed(1)) : 0}%</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
