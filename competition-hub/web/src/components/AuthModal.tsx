import { useState } from 'react'
import { X, LogIn, UserPlus } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { useUI } from '../lib/ui'

export function AuthModal() {
  const { loginOpen, setLoginOpen, toast } = useUI()
  const { login, register } = useAuth()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  if (!loginOpen) return null

  async function submit() {
    setErr('')
    if (username.trim().length < 3) return setErr('用户名至少 3 个字符')
    if (password.length < 6) return setErr('密码至少 6 位')
    setLoading(true)
    try {
      if (mode === 'login') await login(username.trim(), password)
      else await register(username.trim(), password, email.trim())
      toast(mode === 'login' ? '登录成功' : '注册成功', 'ok')
      setLoginOpen(false)
      setUsername('')
      setPassword('')
      setEmail('')
    } catch (e: any) {
      setErr(e?.message || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="glass-strong w-full max-w-sm p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
            {mode === 'login' ? <LogIn size={18} /> : <UserPlus size={18} />}
            {mode === 'login' ? '登录' : '注册'}竞赛雷达
          </h2>
          <button onClick={() => setLoginOpen(false)} className="text-slate-400 hover:text-white">
            <X size={18} />
          </button>
        </div>

        <div className="mb-4 flex gap-2">
          <button
            className={`chip flex-1 justify-center ${mode === 'login' ? 'chip-active' : ''}`}
            onClick={() => setMode('login')}
          >
            登录
          </button>
          <button
            className={`chip flex-1 justify-center ${mode === 'register' ? 'chip-active' : ''}`}
            onClick={() => setMode('register')}
          >
            注册
          </button>
        </div>

        <div className="space-y-3">
          <input
            className="input"
            placeholder="用户名"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          {mode === 'register' && (
            <input
              className="input"
              placeholder="邮箱（可选）"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          )}
          <input
            className="input"
            type="password"
            placeholder="密码"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
        </div>

        {err && <p className="mt-3 text-xs text-neon-pink">{err}</p>}

        <button className="btn-primary mt-5 w-full" onClick={submit} disabled={loading}>
          {loading ? '处理中…' : mode === 'login' ? '登录' : '创建账号'}
        </button>
        <p className="mt-3 text-center text-[11px] text-slate-500">
          登录后即可收藏竞赛、发布赛事信息。
        </p>
      </div>
    </div>
  )
}
