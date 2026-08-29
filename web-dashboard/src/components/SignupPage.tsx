import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function SignupPage({ onNavigateToLogin }: { onNavigateToLogin: () => void }) {
  const { signup } = useAuth();
  
  const [phone, setPhone] = useState('+91');
  const [name, setName] = useState('');
  const [userType, setUserType] = useState<'farmer' | 'official'>('farmer');
  const [role, setRole] = useState('DM');
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true);

    const payload: any = {
      phone,
      name,
      user_type: userType
    };

    if (userType === 'official') {
      payload.role = role;
      payload.wing = 'revenue';
      
      // Basic jurisdiction mapping based on role
      if (role === 'DM') payload.jurisdiction_type = 'district';
      else if (role === 'Tehsildar' || role === 'Naib Tehsildar') payload.jurisdiction_type = 'tehsil';
      else if (role === 'Agriculture Officer') payload.jurisdiction_type = 'block';
      else payload.jurisdiction_type = 'village';
    } else {
      payload.jurisdiction_type = 'village';
    }

    try {
      await signup(payload);
      setSuccess('Account created successfully! You can now log in.');
      setTimeout(() => {
        onNavigateToLogin();
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to sign up');
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
        maxWidth: '450px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
        border: '1px solid var(--border)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h1 style={{ fontSize: '1.8rem', color: 'var(--accent)', margin: '0 0 10px 0' }}>Register</h1>
          <p style={{ color: 'var(--text-2)', fontSize: '0.9rem', margin: 0 }}>
            Create a new Kisan Saathi account
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

        {success && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid var(--green)',
            color: 'var(--green)',
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '20px',
            fontSize: '0.85rem'
          }}>
            ✅ {success}
          </div>
        )}

        <form onSubmit={handleSignup}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', color: 'var(--text-2)' }}>Full Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Enter your name"
              required
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '12px 16px',
                background: 'var(--surface-2)',
                border: '1px solid var(--border-2)',
                borderRadius: '8px',
                color: 'var(--text)',
                fontSize: '1rem',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', color: 'var(--text-2)' }}>Phone Number</label>
            <input
              type="tel"
              value={phone}
              onChange={e => setPhone(e.target.value)}
              placeholder="+91..."
              required
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '12px 16px',
                background: 'var(--surface-2)',
                border: '1px solid var(--border-2)',
                borderRadius: '8px',
                color: 'var(--text)',
                fontSize: '1rem',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', color: 'var(--text-2)' }}>Account Type</label>
            <select
              value={userType}
              onChange={(e) => setUserType(e.target.value as any)}
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '12px 16px',
                background: 'var(--surface-2)',
                border: '1px solid var(--border-2)',
                borderRadius: '8px',
                color: 'var(--text)',
                fontSize: '1rem',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="farmer">👨‍🌾 Farmer</option>
              <option value="official">🏢 Government Official</option>
            </select>
          </div>

          {userType === 'official' && (
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.85rem', color: 'var(--text-2)' }}>Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                disabled={isLoading}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: 'var(--surface-2)',
                  border: '1px solid var(--border-2)',
                  borderRadius: '8px',
                  color: 'var(--text)',
                  fontSize: '1rem',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                <option value="DM">District Magistrate</option>
                <option value="Tehsildar">Tehsildar</option>
                <option value="Naib Tehsildar">Naib Tehsildar</option>
                <option value="Lekhpal/Patwari">Lekhpal / Patwari</option>
                <option value="Agriculture Officer">Agriculture Officer</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || phone.length < 10 || name.trim() === ''}
            className="primary-btn primary-btn--full"
            style={{ marginTop: '10px' }}
          >
            {isLoading ? 'Creating Account...' : 'Sign Up'}
          </button>
          
          <button
            type="button"
            onClick={onNavigateToLogin}
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
            Already have an account? Log in
          </button>
        </form>
      </div>
    </div>
  );
}
