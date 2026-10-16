import { FormEvent, useState } from "react";

type AuthUser = { id: string; name: string; role: string; age_band: string; language: string };

export function AuthScreen({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [registering, setRegistering] = useState(false);
  const [form, setForm] = useState({ name: "", phone: "", pin: "", role: "student", age_band: "18_plus", language: "en" });
  const [error, setError] = useState("");
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    const response = await fetch(`/api/v1/auth/${registering ? "register" : "login"}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(registering ? form : { phone: form.phone, pin: form.pin }),
    });
    const body = await response.json();
    if (!response.ok) { setError(body.detail || "Authentication failed"); return; }
    if (registering) { setRegistering(false); setError("Registration complete. Sign in below."); return; }
    localStorage.setItem("auth_token", body.token);
    localStorage.setItem("current_user", JSON.stringify(body.user));
    onLogin(body.user);
  };
  return <section className="auth-card">
    <div className="auth-copy"><span className="eyebrow">Local work. Visible progress.</span><h1>{registering ? "Create a workspace account." : "Welcome back."}</h1><p>Connect local demand to safe, supervised learning pathways.</p></div>
    <div className="auth-panel"><h2>{registering ? "Create your account" : "Sign in"}</h2><p className="muted">{registering ? "Start with a role and language that fit your work." : "Use your phone and PIN to continue."}</p>
    <form onSubmit={submit}>
      {registering && <label>Name<input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label>}
      <label>Phone<input required inputMode="tel" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} /></label>
      <label>PIN<input required minLength={4} maxLength={6} pattern="\d{4,6}" inputMode="numeric" type="password" value={form.pin} onChange={e => setForm({ ...form, pin: e.target.value })} /></label>
      {registering && <>
        <label>Role<select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}><option value="student">Student</option><option value="employer">Employer</option><option value="facilitator">Facilitator</option></select></label>
        <label>Age band<select value={form.age_band} onChange={e => setForm({ ...form, age_band: e.target.value })}><option value="under_14">Under 14</option><option value="14_17">14–17</option><option value="18_plus">18+</option></select></label>
        <label>Language<select value={form.language} onChange={e => setForm({ ...form, language: e.target.value })}><option value="en">English</option><option value="hi">हिन्दी</option><option value="ta">தமிழ்</option></select></label>
      </>}
      {error && <p className="unknown" role="alert">{error}</p>}
      <button className="primary-button" type="submit">{registering ? "Register" : "Sign in"}</button>
    </form>
    <button className="link-button" onClick={() => { setRegistering(!registering); setError(""); }}>{registering ? "Already registered? Sign in" : "Create an account"}</button>
    </div>
  </section>;
}
