import ChatBox from './components/ChatBox'
import SettingsPanel from './components/SettingsPanel'
import './App.css'

function App() {
  return (
    <div className="app-container">
  <h1 className="text-2xl font-semibold mb-4">Pluto — Chat (demo)</h1>
  <SettingsPanel />
  <ChatBox />
    </div>
  )
}

export default App
