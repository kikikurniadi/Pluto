import express from 'express'
import bodyParser from 'body-parser'

const app = express()
app.use(bodyParser.json())

function randomPrice(base = 10000) {
  const delta = Math.round((Math.random() - 0.5) * base * 0.2)
  return base + delta
}

app.post('/query', (req, res) => {
  const { text } = req.body || {}
  const q = (text || '').toLowerCase()
  if (q.includes('price') || q.includes('harga') || q.includes('berapa')) {
    const coin = q.includes('ethereum') ? 'Ethereum' : q.includes('solana') ? 'Solana' : 'Bitcoin'
    const base = coin === 'Ethereum' ? 1800 : coin === 'Solana' ? 20 : 65000
    const price = randomPrice(base)
    return res.json({ reply: `Harga ${coin} saat ini adalah $${price} USD.` })
  }
  if (q.includes('news') || q.includes('berita') || q.includes('update')) {
    return res.json({ reply: 'Berita terkini: 1) Exchange X mengumkan listing baru. 2) Token Y mengalami lonjakan harga 12%. (mocked)' })
  }
  return res.json({ reply: `Mock reply from server: received "${text}"` })
})

const port = process.env.PORT || 8001
app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`Orchestrator mock listening on http://localhost:${port}`)
})
