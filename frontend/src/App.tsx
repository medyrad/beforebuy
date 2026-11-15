import { useEffect, useRef, useState } from 'react'

import { Questionnaire } from './features/analysis/Questionnaire'
import { ReportView } from './features/analysis/ReportView'
import { createEmptyDraft, draftFromAnalysis, type Draft } from './features/analysis/draft'
import { HistoryView } from './features/history/HistoryView'
import { CopilotApp } from './features/copilot/conversation/CopilotApp'
import { api, ApiError } from './services/api/client'
import type { Analysis, AnalysisInput, AnalysisSummary } from './services/api/types'

type View = 'home' | 'questionnaire' | 'report' | 'history'

const messageFor = (error: unknown) => {
  if (error instanceof ApiError) {
    if (error.status === 404) return 'این تحلیل در دسترس نیست. ممکن است منقضی یا پاک شده باشد، یا به نشست دیگری تعلق داشته باشد.'
    if (error.status === 409) return 'نسخهٔ تحلیل تغییر کرده است؛ تازه‌ترین نسخه دریافت شد. دوباره اقدام کنید.'
    return error.message
  }
  if (error instanceof DOMException && error.name === 'AbortError') return null
  return 'ارتباط با سرویس برقرار نشد. وضعیت Docker backend را بررسی و دوباره تلاش کنید.'
}

function Home({ onStart, onHistory, count }: { onStart: () => void; onHistory: () => void; count: number }) {
  return <section className="home">
    <div className="home-copy">
      <p className="eyebrow">تصمیم روشن‌تر، بدون فشار برای خرید</p>
      <h1>قبل از خرید، نیاز و بودجه‌ات را کنار هم ببین.</h1>
      <p className="lead">با چند پاسخ کوتاه، دلیل خرید یا تعویض، تناسب با بودجه و ابهام‌های مدل انتخابی را جداگانه مرور کن.</p>
      <div className="button-row"><button className="button primary large" onClick={onStart}>خریدم را بررسی کن</button><button className="button ghost" onClick={onHistory}>تاریخچه{count > 0 ? ` (${count.toLocaleString('fa-IR')})` : ''}</button></div>
      <p className="privacy-note">بدون حساب کاربری؛ دسترسی تحلیل‌ها به نشست همین مرورگر وابسته است.</p>
    </div>
    <aside className="promise-card" aria-label="محدودهٔ تحلیل">
      <h2>این تحلیل چه می‌گوید؟</h2>
      <ol><li><span>۱</span>آیا خرید یا تعویض با وضعیت فعلی توجیه دارد؟</li><li><span>۲</span>آیا قیمت در سقف بودجهٔ اعلام‌شده است؟</li><li><span>۳</span>دربارهٔ مناسب‌بودن خود مدل چه چیزهایی هنوز نامعلوم است؟</li></ol>
      <p>هیچ امتیاز عددی، مشخصات ساختگی یا توصیهٔ فروشگاهی نمایش داده نمی‌شود.</p>
    </aside>
  </section>
}

function LegacyApp() {
  const [view, setView] = useState<View>('home')
  const [history, setHistory] = useState<AnalysisSummary[]>([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [draft, setDraft] = useState<Draft>(createEmptyDraft)
  const [editing, setEditing] = useState(false)
  const [pending, setPending] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [formErrors, setFormErrors] = useState<Record<string, string[]>>({})
  const loadSequence = useRef(0)

  const navigate = (next: View, id?: string) => {
    const url = id ? `/legacy?analysis=${encodeURIComponent(id)}` : next === 'history' ? '/legacy?view=history' : '/legacy'
    window.history.pushState({}, '', url)
    setView(next)
  }

  const refreshHistory = async (signal?: AbortSignal) => {
    const result = await api.list(signal)
    setHistory(result.items)
    setHistoryError(null)
  }

  const openAnalysis = async (id: string, push = true) => {
    const sequence = ++loadSequence.current
    setPending('open')
    setNotice(null)
    try {
      const value = await api.get(id)
      if (sequence !== loadSequence.current) return
      setAnalysis(value)
      setView('report')
      if (push) navigate('report', id)
    } catch (error) {
      const message = messageFor(error)
      if (message && sequence === loadSequence.current) { setNotice(message); setView('history') }
    } finally {
      if (sequence === loadSequence.current) setPending(null)
    }
  }

  useEffect(() => {
    const controller = new AbortController()
    const initialize = async () => {
      try {
        await api.bootstrap(controller.signal)
        const listed = await api.list(controller.signal)
        setHistory(listed.items)
        setHistoryError(null)
        const parameters = new URLSearchParams(window.location.search)
        const id = parameters.get('analysis')
        if (id) {
          const value = await api.get(id, controller.signal)
          setAnalysis(value)
          setView('report')
        }
        else if (parameters.get('view') === 'history') setView('history')
      } catch (error) {
        const message = messageFor(error)
        if (message) setHistoryError(message)
      } finally { setHistoryLoading(false) }
    }
    void initialize()
    return () => { controller.abort(); loadSequence.current += 1 }
  }, [])

  const start = () => {
    setDraft(createEmptyDraft())
    setEditing(false)
    setFormErrors({})
    setNotice(null)
    navigate('questionnaire')
  }

  const submit = async (input: AnalysisInput) => {
    if (pending) return
    setPending('submit'); setFormErrors({}); setNotice(null)
    try {
      const value = editing && analysis ? await api.update(analysis, input) : await api.create(input)
      await refreshHistory()
      setAnalysis(value); setEditing(false); setView('report')
      window.history.replaceState({}, '', `/legacy?analysis=${encodeURIComponent(value.id)}`)
    } catch (error) {
      if (error instanceof ApiError) setFormErrors(error.fieldErrors)
      const message = messageFor(error)
      if (message) setNotice(message)
      if (error instanceof ApiError && error.status === 409 && analysis) await openAnalysis(analysis.id, false)
    } finally { setPending(null) }
  }

  const edit = () => {
    if (!analysis) return
    setDraft(draftFromAnalysis(analysis)); setEditing(true); setFormErrors({}); setNotice(null); navigate('questionnaire')
  }

  const retry = async () => {
    if (!analysis || pending) return
    setPending('retry'); setNotice(null)
    try { setAnalysis(await api.retry(analysis)) }
    catch (error) {
      const message = messageFor(error); if (message) setNotice(message)
      if (error instanceof ApiError && error.status === 409) await openAnalysis(analysis.id, false)
    } finally { setPending(null) }
  }

  const rate = async (rating: number) => {
    if (!analysis || pending) return
    setPending('feedback')
    try {
      const feedback = await api.rate(analysis, rating)
      setAnalysis({ ...analysis, report: { ...analysis.report, feedback } })
    } catch (error) { const message = messageFor(error); if (message) setNotice(message) }
    finally { setPending(null) }
  }

  const removeRating = async () => {
    if (!analysis || pending) return
    setPending('feedback')
    try { await api.removeRating(analysis); setAnalysis({ ...analysis, report: { ...analysis.report, feedback: null } }) }
    catch (error) { const message = messageFor(error); if (message) setNotice(message) }
    finally { setPending(null) }
  }

  const deleteOne = async (id: string) => {
    if (pending) return
    setPending('delete')
    try {
      loadSequence.current += 1
      await api.delete(id)
      setHistory((items) => items.filter((item) => item.id !== id))
      if (analysis?.id === id) { setAnalysis(null); navigate('history') }
      setNotice('تحلیل از تاریخچهٔ فعال پاک شد.')
    } catch (error) { const message = messageFor(error); if (message) setNotice(message) }
    finally { setPending(null) }
  }

  const clear = async () => {
    if (pending) return
    setPending('clear')
    try { loadSequence.current += 1; await api.clear(); setHistory([]); setAnalysis(null); setNotice('تاریخچهٔ فعال این مرورگر پاک شد.') }
    catch (error) { const message = messageFor(error); if (message) setNotice(message) }
    finally { setPending(null) }
  }

  return <>
    <a className="skip-link" href="#main">رفتن به محتوای اصلی</a>
    <header className="site-header"><button className="brand" onClick={() => navigate('home')} aria-label="صفحهٔ آغاز قبل از خرید"><span className="brand-mark">ب</span><span>قبل از خرید</span></button><nav aria-label="ناوبری اصلی"><a href="/">دستیار خرید جدید</a><button onClick={start}>تحلیل جدید</button><button onClick={() => navigate('history')}>تاریخچه</button></nav></header>
    <main id="main" tabIndex={-1}>
      {notice && <div className="notice" role="status"><span>{notice}</span><button type="button" onClick={() => setNotice(null)} aria-label="بستن پیام">×</button></div>}
      {historyError && view === 'home' && <div className="form-banner error" role="alert">{historyError}</div>}
      {view === 'home' && <Home onStart={start} onHistory={() => navigate('history')} count={history.length} />}
      {view === 'questionnaire' && <Questionnaire initialDraft={draft} onSubmit={submit} onCancel={() => navigate(analysis ? 'report' : 'home', analysis?.id)} submitting={pending === 'submit'} serverErrors={formErrors} />}
      {view === 'report' && analysis && <ReportView analysis={analysis} onEdit={edit} onRetry={retry} onRate={rate} onRemoveRating={removeRating} pendingAction={pending} />}
      {view === 'history' && <HistoryView items={history} loading={historyLoading || pending === 'open'} error={historyError} onOpen={(id) => void openAnalysis(id)} onDelete={(id) => void deleteOne(id)} onClear={() => void clear()} />}
    </main>
    <footer className="site-footer"><p>این ابزار تصمیم‌یار است، نه مشاورهٔ مالی یا تأیید فنی محصول.</p><span>نسخهٔ آزمایشی · تلفن همراه</span></footer>
  </>
}

export default function App() {
  const query = new URLSearchParams(window.location.search)
  const legacy = window.location.pathname === '/legacy' || query.has('analysis') || query.get('view') === 'history'
  return legacy ? <LegacyApp /> : <CopilotApp />
}
