import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage({ onNavigateToSignup }: { onNavigateToSignup?: () => void }) {
  const { requestOTP, login } = useAuth();
  
  const [phone, setPhone] = useState('+91');
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [devCode, setDevCode] = useState<string | undefined>(undefined);

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    setDevCode(undefined);
    try {
      const res = await requestOTP(phone);
      setStep('otp');
      if (res.dev_code) {
        setDevCode(res.dev_code);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to request OTP');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await login(phone, otp);
    } catch (err: any) {
      setError(err.message || 'Invalid OTP');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      background: 'var(--bg)',
      color: 'var(--text)'
    }}>
      <div style={{
        background: 'var(--surface)',
        padding: '30px',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '400px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
        border: '1px solid var(--border)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h1 style={{ fontSize: '1.8rem', color: 'var(--accent)', margin: '0 0 10px 0' }}>Kisan Saathi</h1>
          <p style={{ color: 'var(--text-2)', fontSize: '0.9rem', margin: 0 }}>
            Login to access your dashboard
          </p>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid var(--red)',
            color: 'var(--red)',
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '20px',
            fontSize: '0.85rem'
          }}>
            ⚠️ {error}
          </div>
        )}

        {devCode && (
          <div style={{
            background: 'var(--orange-dim)',
            border: '1px solid var(--orange)',
            color: 'var(--orange)',
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '20px',
            fontSize: '0.85rem',
            textAlign: 'center'
          }}>
            🛠️ <strong>Dev Mode</strong>: Your OTP is <strong>{devCode}</strong>
          </div>
        )}

        {step === 'phone' ? (
          <form onSubmit={handleRequestOTP} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
              <button
                type="button"
                onClick={(e) => {
                  setPhone('+91124567890');
                  // We must defer the submit slightly so state updates
                  setTimeout(() => {
                    const event = new Event('submit', { bubbles: true, cancelable: true });
                    e.currentTarget.form?.dispatchEvent(event);
                  }, 50);
                }}
                style={{
                  flex: 1,
                  background: 'var(--surface-2)',
                  color: 'var(--text)',
                  border: '1px solid var(--border)',
                  padding: '10px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '0.85rem'
                }}
              >
                🌾 Login as Farmer
              </button>
              <button
                type="button"
                onClick={(e) => {
                  setPhone('+91123456789');
                  setTimeout(() => {
                    const event = new Event('submit', { bubbles: true, cancelable: true });
                    e.currentTarget.form?.dispatchEvent(event);
                  }, 50);
                }}
                style={{
                  flex: 1,
                  background: 'var(--surface-2)',
                  color: 'var(--text)',
                  border: '1px solid var(--border)',
                  padding: '10px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '0.85rem'
                }}
              >
                🏛️ Login as Official
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '0.9rem', color: 'var(--text-2)' }}>Phone Number</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91..."
                disabled={isLoading}
                style={{
                  background: 'var(--bg)',
                  border: '1px solid var(--border-2)',
                  color: 'var(--text)',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  outline: 'none'
                }}
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || phone.length < 10}
              className="primary-btn primary-btn--full"
            >
              {isLoading ? 'Sending...' : 'Request OTP'}
            </button>
            {onNavigateToSignup && (
              <button
                type="button"
                onClick={onNavigateToSignup}
                style={{
                  width: '100%',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-2)',
                  marginTop: '16px',
                  cursor: 'pointer',
                  fontSize: '0.85rem'
                }}
              >
                Don't have an account? Sign up
              </button>
            )}
          </form>
        ) : (
          <form onSubmit={handleVerifyOTP}>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', color: 'var(--text-2)' }}>Enter OTP</label>
              <input
                type="text"
                value={otp}
                onChange={e => setOtp(e.target.value)}
                placeholder="6-digit code"
                disabled={isLoading}
                maxLength={6}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: 'var(--surface-2)',
                  border: '1px solid var(--border-2)',
                  borderRadius: '8px',
                  color: 'var(--text)',
                  fontSize: '1rem',
                  outline: 'none',
                  letterSpacing: '4px',
                  textAlign: 'center'
                }}
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || otp.length !== 6}
              className="primary-btn primary-btn--full"
            >
              {isLoading ? 'Verifying...' : 'Verify & Login'}
            </button>
            {devCode && (
              <button
                type="button"
                onClick={(e) => {
                  setOtp(devCode);
                  setTimeout(() => {
                    const event = new Event('submit', { bubbles: true, cancelable: true });
                    e.currentTarget.form?.dispatchEvent(event);
                  }, 50);
                }}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: 'var(--surface-2)',
                  color: 'var(--text)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '1rem',
                  cursor: 'pointer',
                  marginTop: '10px'
                }}
              >
                🪄 Auto-Fill OTP & Login
              </button>
            )}
            <button
              type="button"
              onClick={() => { setStep('phone'); setOtp(''); setDevCode(undefined); setError(''); }}
              style={{
                width: '100%',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-2)',
                marginTop: '16px',
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              ← Back to Phone Number
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
