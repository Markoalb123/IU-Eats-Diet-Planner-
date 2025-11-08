import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

function App() {
  const [diets, setDiets] = useState([])
  const [availableItems, setAvailableItems] = useState([])
  const [itemDraft, setItemDraft] = useState('')
  const [weeklyGoal, setWeeklyGoal] = useState('')
  const [dietChoice, setDietChoice] = useState('')
  const [customDiet, setCustomDiet] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [plan, setPlan] = useState(null)
  const [history, setHistory] = useState([])
  const [historyError, setHistoryError] = useState('')

  useEffect(() => {
    loadDiets()
    loadHistory()
  }, [])

  async function loadDiets() {
    try {
      const response = await fetch(`${API_BASE}/diets`)
      if (!response.ok) throw new Error('Unable to load diet options')
      const data = await response.json()
      setDiets(data)
    } catch (err) {
      console.error(err)
      setError(err.message ?? 'Failed to load diet options')
    }
  }

  async function loadHistory() {
    try {
      const response = await fetch(`${API_BASE}/history`)
      if (!response.ok) throw new Error('Unable to load saved plans')
      const data = await response.json()
      setHistory(data)
      setHistoryError('')
    } catch (err) {
      console.error(err)
      setHistoryError(err.message ?? 'Failed to load saved plans')
    }
  }

  const canSubmit = useMemo(() => {
    if (!weeklyGoal || !dietChoice) return false
    if (dietChoice === 'Custom Diet' && !customDiet.trim()) return false
    return availableItems.length > 0
  }, [availableItems.length, weeklyGoal, dietChoice, customDiet])

  function handleAddItem() {
    const trimmed = itemDraft.trim()
    if (!trimmed) return
    setAvailableItems((prev) => [...prev, trimmed])
    setItemDraft('')
  }

  function handleRemoveItem(index) {
    setAvailableItems((prev) => prev.filter((_, idx) => idx !== index))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!canSubmit) return

    setLoading(true)
    setError('')

    try {
      const response = await fetch(`${API_BASE}/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          available_items: availableItems,
          weekly_goal: weeklyGoal,
          diet_choice: dietChoice,
          custom_diet_description:
            dietChoice === 'Custom Diet' ? customDiet.trim() : null,
        }),
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail ?? 'The AI service returned an error')
      }

      setPlan(payload.plan)
      await loadHistory()
    } catch (err) {
      console.error(err)
      setError(err.message ?? 'Something went wrong while generating the plan')
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    setAvailableItems([])
    setItemDraft('')
    setWeeklyGoal('')
    setDietChoice('')
    setCustomDiet('')
    setPlan(null)
    setError('')
  }

  function handleLoadHistory(entry) {
    setPlan(entry.plan)
  }

  return (
    <div className="app-shell">
      <header className="masthead">
        <div>
          <p className="eyebrow">Weekly Diet Planner</p>
          <h1>Translate your goals into a chef-curated plan</h1>
          <p className="lede">
            List the food you already own, pick your focus for the week, and let the AI chef build a
            tailored weekday lineup—complete with rationale, recipes, and nutrition.
          </p>
        </div>
        <div className="actions">
          {plan && (
            <a className="ghost" href={`${API_BASE}/dashboard`} target="_blank" rel="noreferrer">
              Open Dashboard
            </a>
          )}
          {plan && (
            <button type="button" className="ghost" onClick={handleReset}>
              Start Over
            </button>
          )}
        </div>
      </header>

      <main className="layout">
        <section className="card">
          <h2>Step 1 · Your Pantry & Preferences</h2>

          <form className="preferences" onSubmit={handleSubmit}>
            <div className="input-group">
              <label htmlFor="item-draft">Items Available</label>
              <div className="list-input">
                <div className="list-input-controls">
                  <input
                    id="item-draft"
                    type="text"
                    value={itemDraft}
                    onChange={(event) => setItemDraft(event.target.value)}
                    placeholder="e.g. tomatoes"
                    disabled={loading}
                  />
                  <button type="button" onClick={handleAddItem} disabled={!itemDraft.trim() || loading}>
                    Add
                  </button>
                </div>
                <p className="hint">Add each ingredient separately; we'll build the list for you.</p>
                <ul className="chip-list">
                  {availableItems.map((item, index) => (
                    <li key={`${item}-${index}`} className="chip">
                      <span>{item}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(index)}
                        aria-label={`Remove ${item}`}
                        disabled={loading}
                      >
                        &times;
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="input-group">
              <label htmlFor="weekly-goal">Weekly Goal</label>
              <textarea
                id="weekly-goal"
                value={weeklyGoal}
                onChange={(event) => setWeeklyGoal(event.target.value)}
                placeholder="e.g. increase protein intake, cut down on sugar"
                rows={3}
                disabled={loading}
                required
              />
            </div>

            <div className="input-group">
              <label htmlFor="diet-choice">Diet Preference</label>
              <select
                id="diet-choice"
                value={dietChoice}
                onChange={(event) => setDietChoice(event.target.value)}
                disabled={loading}
                required
              >
                <option value="" disabled>
                  Select a diet
                </option>
                {diets.map((diet) => (
                  <option key={diet} value={diet}>
                    {diet}
                  </option>
                ))}
              </select>
            </div>

            {dietChoice === 'Custom Diet' && (
              <div className="input-group">
                <label htmlFor="custom-diet">Describe Your Diet</label>
                <textarea
                  id="custom-diet"
                  value={customDiet}
                  onChange={(event) => setCustomDiet(event.target.value)}
                  placeholder="Summarize your personal dietary approach"
                  rows={3}
                  disabled={loading}
                  required
                />
              </div>
            )}

            {error && <p className="error">{error}</p>}

            <button type="submit" disabled={!canSubmit || loading}>
              {loading ? 'Generating plan…' : 'Generate Weekly Plan'}
            </button>
          </form>
        </section>

        <section className="card info">
          <h2>What We Craft</h2>
          <ul>
            <li>
              <strong>Meal Variety</strong> · Distinct dishes for every weekday, pairing pantry items and
              suggested additions.
            </li>
            <li>
              <strong>Why It Works</strong> · Context for each meal explaining how it supports your goal and diet.
            </li>
            <li>
              <strong>Cooking Roadmap</strong> · Recipes broken into easy steps so you can get cooking instantly.
            </li>
            <li>
              <strong>Nutritional Snapshot</strong> · At-a-glance calories, macros, and key micronutrients.
            </li>
          </ul>

          {plan && (
            <div className="downloads">
              <a className="ghost" href={`${API_BASE}/plan/csv`} target="_blank" rel="noreferrer">
                Download CSV
              </a>
              <a className="ghost" href={`${API_BASE}/dashboard`} target="_blank" rel="noreferrer">
                View Dashboard
              </a>
            </div>
          )}
        </section>
      </main>

      {plan && (
        <section className="plan-grid">
          {plan.map((entry, index) => (
            <article className="plan-card" key={`${entry.day}-${index}`}>
              <header>
                <span className="day">{entry.day}</span>
                <span className="sequence">Day {index + 1}</span>
              </header>
              <h3>{entry.meal}</h3>
              <section className="segment">
                <h4>Why this meal</h4>
                <p>{entry.rationale}</p>
              </section>
              <section className="segment">
                <h4>Recipe</h4>
                {renderRecipe(entry.recipe)}
              </section>
              <section className="segment">
                <h4>Nutritional Value</h4>
                <p>{entry.nutritional_value}</p>
              </section>
            </article>
          ))}
        </section>
      )}

      <section className="card history-card">
        <h2>Saved Plans</h2>
        {historyError && <p className="error">{historyError}</p>}
        {history.length === 0 && !historyError && <p>No saved plans yet. Generate one to get started.</p>}
        {history.length > 0 && (
          <ul className="history-list">
            {history.map((entry) => (
              <li key={entry.id} className="history-item">
                <div>
                  <p className="history-date">{formatDate(entry.created_at)}</p>
                  <p className="history-goal">Goal: {entry.weekly_goal || '—'}</p>
                  <p className="history-diet">Diet: {entry.diet_descriptor || '—'}</p>
                </div>
                <button type="button" className="ghost" onClick={() => handleLoadHistory(entry)}>
                  View Plan
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

function renderRecipe(text) {
  if (!text.includes('\n')) {
    return <p>{text}</p>
  }

  const steps = text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  return (
    <ol>
      {steps.map((step, index) => (
        <li key={`${step}-${index}`}>{step}</li>
      ))}
    </ol>
  )
}

function formatDate(value) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch (err) {
    return value
  }
}

export default App
