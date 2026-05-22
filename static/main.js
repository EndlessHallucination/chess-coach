var config = {
    draggable: true,
    onDrop: onDrop,
    dropOffBoard: 'snapback',
    position: 'start',
    pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png'
}
var board = Chessboard('myBoard', config)

document.getElementById('myBoard').style.width = '100%'
board.resize()

let lastMove = null


async function sendMove(source, target) {
    const url = "http://127.0.0.1:5000/move"
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ move: source + target }),
        })
        if (!response.ok) throw new Error("Response status: " + response.status)
        const data = await response.json()
        board.position(data.fen)
        updateStatus(data.fen)
        const turn = data.fen.split(' ')[1]
        checkGameStatus()
        const color = turn === 'w' ? 'black' : 'white'
        lastMove = { move: source + target, fen: data.fen, color: color }
        updateHistory()
    } catch (error) {
        console.error(error.message)
    }
}

function onDrop(source, target) {
    sendMove(source, target)
    return 'snapback'
}

async function resetBoard() {
    const url = "http://127.0.0.1:5000/board/reset"
    try {
        const response = await fetch(url, { method: "POST" })
        if (!response.ok) throw new Error("Response status: " + response.status)
        const data = await response.json()
        board.position(data.fen)
        updateStatus(data.fen)
        lastMove = null
        // Clear hint fields
        setHintField('hintText', '—')
        setHintField('hintConcepts', '—')
        setHintField('hintBestMove', '—')
        setHintField('hintExplanation', '—')
        document.getElementById('analysisDisplay').innerText = '—'
        updateHistory()
        board.draggable = true
    } catch (error) {
        console.error(error.message)
    }
}

function updateStatus(fen) {
    const turn = fen.split(' ')[1]
    const isWhite = turn === 'w'
    document.getElementById('status').innerText = isWhite ? 'White to move' : 'Black to move'
    const dot = document.getElementById('turn-dot')
    dot.classList.toggle('black', !isWhite)
}

// Helper: set a hint value span by its ID
function setHintField(id, text) {
    document.getElementById(id).innerText = text
}

async function getHint() {
    const url = "http://127.0.0.1:5000/board/hint"
    const btn = document.getElementById('hintBtn')
    btn.disabled = true
    btn.innerText = 'Thinking...'
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
        })
        if (!response.ok) throw new Error("Response status: " + response.status)
        const data = await response.json()
        const hint = parseHint(data.hint)
        setHintField('hintText', hint.hint || '—')
        setHintField('hintConcepts', hint.concepts || '—')
        setHintField('hintBestMove', hint.bestMove || '—')
        setHintField('hintExplanation', hint.explanation || '—')
    } catch (error) {
        console.error(error.message)
    } finally {
        btn.disabled = false
        btn.innerText = 'Get Hint'
    }
}

function parseHint(text) {
    const parts = text.split(/HINT:|CONCEPTS:|BEST MOVE:|EXPLANATION:/)
    return {
        hint: parts[1]?.trim() || '',
        concepts: parts[2]?.trim() || '',
        bestMove: parts[3]?.trim() || '',
        explanation: parts[4]?.trim() || ''
    }
}

let analyzing = false

async function analyzeMove(move, fen, color) {
    const url = "http://127.0.0.1:5000/board/analyze"
    if (analyzing) return
    analyzing = true
    document.getElementById('analysisDisplay').innerText = 'Analyzing your move...'
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ move, fen, color })
        })
        if (!response.ok) throw new Error("Response status: " + response.status)
        const data = await response.json()
        document.getElementById('analysisDisplay').innerText = data.response
    } catch (error) {
        console.error(error.message)
    } finally {
        analyzing = false
    }
}

function flipBoard() {
    board.flip()
}

async function updateHistory(){
const url = "http://127.0.0.1:5000/board/history"
    try {
        const response = await fetch(url, {
            method: "GET",
            headers: { 'Content-Type': 'application/json' },
        })
        if (!response.ok) throw new Error("Response status: " + response.status)
        const data = await response.json()
    moveString = ""
    for (let i = 0; i < data.moves.length; i += 2) {
        const white = data.moves[i]
        const black = data.moves[i + 1] || ''
        const moveNum = (i / 2) + 1
        moveString += `${moveNum}. ${white} ${black}  `
    }
    document.getElementById('moveHistory').innerText = moveString
    } catch (error) {
        console.error(error.message)
    }
}

async function undoMove() {
     const url = "http://127.0.0.1:5000/board/undo"
     try {
        const response = await fetch(url, {method: "POST"})
        if (!response.ok) throw new Error("Response status: " + response.status)
        const data = await response.json()
        board.position(data.fen)
        updateStatus(data.fen)
        updateHistory()
        const turn = data.fen.split(' ')[1]
        const color = turn === 'w' ? 'black' : 'white'
        lastMove = { move: null, fen: data.fen, color: color }
     } catch (error) {
        console.error(error.message)
     }
}

async function checkGameStatus() {
    const url = "http://127.0.0.1:5000/board/status"

    try {
        const response = await fetch(url, {
            method: "GET"
        })

        if (!response.ok) {
            throw new Error("Response status: " + response.status)
        }

        const data = await response.json()

        const statusDiv = document.getElementById("gameStatus")

        if (data.checkmate) {
            const winner = data.turn === "white" ? "Black" : "White"
            statusDiv.textContent = `Checkmate! ${winner} wins!`
        }
        else if (data.stalemate) {
            statusDiv.textContent = "Draw by stalemate!"
        }
        else if (data.check) {
            const color = data.turn === "white" ? "Black" : "White"
            statusDiv.textContent = `${color} Checked!`
        }
        else {
            statusDiv.textContent = ""
        }

        if (data.game_over) {
            board.draggable = false
        }

    } catch (error) {
        console.error("Error checking game status:", error)
    }
}


document.getElementById('resetBtn').addEventListener('click', resetBoard)
document.getElementById('flipBtn').addEventListener('click', flipBoard)
document.getElementById('hintBtn').addEventListener('click', getHint)
document.getElementById('undoBtn').addEventListener('click', undoMove)
document.getElementById('analyzeBtn').addEventListener('click', () => {
    if (!lastMove) return
    const playingAs = document.getElementById('playingAs').value
    if (playingAs !== 'both' && lastMove.color !== playingAs) return
    analyzeMove(lastMove.move, lastMove.fen, lastMove.color)
})