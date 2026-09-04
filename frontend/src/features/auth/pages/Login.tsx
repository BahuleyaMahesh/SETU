import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../app/auth/AuthProvider';
import { AppLogo } from '../../../shared/components/AppLogo';
import { Button } from '../../../shared/components/Button';
import { ThemeToggle } from '../../../shared/components/ThemeToggle';
import {
  ShieldCheck,
  Users,
  UserCheck,
  Building2,
  ArrowRight,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Sprout
} from 'lucide-react';

export const Login: React.FC = () => {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [hospitalName, setHospitalName] = useState('');
  const [hospitals, setHospitals] = useState<{ id: string; name: string }[]>([]);
  const [selectedHospitalId, setSelectedHospitalId] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [selectedRole, setSelectedRole] = useState<'patient' | 'asha' | 'hospital'>('patient');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetch('/api/v1/auth/hospitals')
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setHospitals(Array.isArray(data) ? data : []))
      .catch(() => setHospitals([]));
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await register(
        email,
        password,
        fullName,
        phone,
        selectedRole,
        selectedRole === 'hospital' ? hospitalName : undefined,
        selectedRole === 'patient' ? selectedHospitalId || undefined : undefined
      );
    } catch (err: any) {
      setError(err.message || 'Could not create account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (next: 'login' | 'signup') => {
    setMode(next);
    setError('');
  };

  const roleOptions = [
    {
      id: 'patient',
      title: 'Patient',
      subtitle: 'Your health companion',
      icon: Users,
      bgColor: 'bg-sky-50/90 hover:bg-sky-100/90 border-sky-100/80 backdrop-blur-md',
      activeBorder: 'ring-2 ring-sky-500 border-sky-400 bg-sky-100/95 shadow-md backdrop-blur-md',
      iconBg: 'bg-sky-600 text-white',
      arrowBg: 'bg-white text-sky-600',
    },
    {
      id: 'asha',
      title: 'ASHA Worker',
      subtitle: 'Field care made easier',
      icon: UserCheck,
      bgColor: 'bg-emerald-50/90 hover:bg-emerald-100/90 border-emerald-100/80 backdrop-blur-md',
      activeBorder: 'ring-2 ring-emerald-500 border-emerald-400 bg-emerald-100/95 shadow-md backdrop-blur-md',
      iconBg: 'bg-emerald-600 text-white',
      arrowBg: 'bg-white text-emerald-600',
    },
    {
      id: 'hospital',
      title: 'Hospital',
      subtitle: 'Better patient outcomes',
      icon: Building2,
      bgColor: 'bg-purple-50/90 hover:bg-purple-100/90 border-purple-100/80 backdrop-blur-md',
      activeBorder: 'ring-2 ring-purple-500 border-purple-400 bg-purple-100/95 shadow-md backdrop-blur-md',
      iconBg: 'bg-purple-600 text-white',
      arrowBg: 'bg-white text-purple-600',
    },
  ] as const;

  return (
    <div className="min-h-screen bg-[#f7fafc] flex flex-col lg:flex-row relative overflow-hidden font-sans text-slate-800">
      
      {/* LEFT HERO & LANDING SECTION */}
      <div className="always-light lg:w-[54%] min-h-[620px] lg:min-h-screen relative flex flex-col justify-between p-6 sm:p-10 lg:p-14 overflow-hidden bg-gradient-to-br from-[#ebf4fa] via-[#e4f0f8] to-[#dceaf4]">
        
        {/* Rural Care Background Image - Framed in bottom section exactly as in target design */}
        <div className="absolute inset-x-0 bottom-0 h-[62%] pointer-events-none overflow-hidden">
          <img
            src="/rural-care-bg.jpg"
            alt="Rural Healthcare Worker"
            className="w-full h-full object-cover object-bottom filter saturate-[1.08] contrast-[1.02]"
          />
          {/* Smooth Soft Gradient Fade transition into upper sky-blue background */}
          <div className="absolute inset-0 bg-gradient-to-t from-transparent via-[#e4f0f8]/35 to-[#ebf4fa]" />
        </div>

        {/* Organic Curved Wave Mask Divider between Left Hero and Right Login */}
        <div className="absolute top-0 right-0 bottom-0 w-32 pointer-events-none hidden lg:block z-10">
          <svg className="h-full w-full text-[#f7fafc] fill-current" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path d="M100,0 C30,35 70,65 100,100 Z" />
          </svg>
        </div>

        {/* Top Header / Logo */}
        <div className="relative z-20 flex items-center justify-between">
          <div className="bg-white/80 backdrop-blur-md p-2 rounded-2xl border border-white/80 shadow-xs inline-block">
            <AppLogo showText={false} size="lg" />
          </div>
        </div>

        {/* Hero Content */}
        <div className="relative z-20 max-w-xl my-auto py-6 sm:py-8 space-y-5">
          <div className="space-y-2.5">
            <h1 className="text-4xl sm:text-5xl lg:text-[3.5rem] font-black text-slate-900 tracking-tight leading-[1.1]">
              Care <br />
              <span className="text-[#3b82f6]">Closer</span> <span className="text-[#059669]">Home</span>
            </h1>
            <p className="text-base sm:text-lg text-slate-600 font-medium tracking-wide">
              Supporting healthier lives after discharge
            </p>
          </div>

          {/* Role Selection Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            {roleOptions.map((role) => {
              const Icon = role.icon;
              const isSelected = selectedRole === role.id;
              return (
                <div
                  key={role.id}
                  onClick={() => setSelectedRole(role.id as any)}
                  className={`p-3.5 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between gap-3 ${
                    isSelected ? role.activeBorder : `${role.bgColor} border-slate-200/60 shadow-xs`
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className={`p-2 rounded-xl ${role.iconBg} shadow-xs`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center transition-transform ${role.arrowBg} ${isSelected ? 'translate-x-0.5' : ''}`}>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900">{role.title}</h3>
                    <p className="text-[10px] text-slate-500 font-medium leading-tight mt-0.5">{role.subtitle}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Hero Tag */}
        <div className="relative z-20 pt-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/65 backdrop-blur-md border border-white/20 text-white text-[11px] font-semibold shadow-md">
            <Sprout className="w-3.5 h-3.5 text-emerald-400" />
            <span>Stronger Communities • Healthier Tomorrows</span>
          </div>
        </div>
      </div>

      {/* RIGHT LOGIN PANEL SECTION */}
      <div className="lg:w-[46%] flex flex-col justify-between p-6 sm:p-10 lg:p-14 bg-[#f7fafc] dark:bg-slate-950 relative z-20 transition-colors">

        {/* Top Security Badge */}
        <div className="flex justify-end items-center gap-2 mb-4">
          <ThemeToggle />
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-400 border border-emerald-200/80 dark:border-emerald-800 text-xs font-semibold shadow-xs">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Secure • Private • Trusted</span>
          </div>
        </div>

        {/* Main Login Form Card */}
        <div className="max-w-md w-full mx-auto my-auto">
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 sm:p-10 border border-slate-100 dark:border-slate-800 shadow-xl shadow-slate-200/60 dark:shadow-slate-950/60 space-y-6 transition-colors">

            {/* Header */}
            <div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
                {mode === 'login' ? 'Welcome Back' : 'Create Account'}
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 font-medium">
                {mode === 'login' ? 'Sign in to your account' : `Sign up as a ${selectedRole === 'asha' ? 'ASHA Worker' : selectedRole}`}
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl font-medium">
                {error}
              </div>
            )}

            {mode === 'login' ? (
              <form onSubmit={handleLogin} className="space-y-4.5">
                {/* Email */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Email
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      placeholder="name@domain.com"
                      className="w-full pl-10 pr-4 py-3 bg-slate-50/70 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white dark:focus:bg-slate-800 text-sm placeholder-slate-400 dark:placeholder-slate-500 font-medium transition-all"
                    />
                  </div>
                </div>

                {/* Password */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Password
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      placeholder="Enter your password"
                      className="w-full pl-10 pr-10 py-3 bg-slate-50/70 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white dark:focus:bg-slate-800 text-sm placeholder-slate-400 dark:placeholder-slate-500 font-medium transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={loading}
                  isLoading={loading}
                  className="w-full bg-[#3b82f6] hover:bg-[#2563eb] text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-sky-500/25 text-sm flex items-center justify-center gap-2 mt-2"
                >
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </form>
            ) : (
              <form onSubmit={handleSignup} className="space-y-4">
                {/* Role picker */}
                <div className="grid grid-cols-3 gap-2">
                  {(['patient', 'asha', 'hospital'] as const).map((r) => (
                    <button
                      type="button"
                      key={r}
                      onClick={() => setSelectedRole(r)}
                      className={`py-2 rounded-xl text-xs font-bold border transition-all capitalize ${
                        selectedRole === r
                          ? 'bg-sky-600 border-sky-600 text-white shadow-sm'
                          : 'bg-slate-50 dark:bg-slate-800/70 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300'
                      }`}
                    >
                      {r === 'asha' ? 'ASHA' : r}
                    </button>
                  ))}
                </div>

                {/* Full name */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    placeholder="Your name"
                    className="w-full px-3.5 py-3 bg-slate-50/70 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white dark:focus:bg-slate-800 text-sm placeholder-slate-400 dark:placeholder-slate-500 font-medium transition-all"
                  />
                </div>

                {/* Phone */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Phone
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    required
                    placeholder="+91-90000-00000"
                    className="w-full px-3.5 py-3 bg-slate-50/70 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white dark:focus:bg-slate-800 text-sm placeholder-slate-400 dark:placeholder-slate-500 font-medium transition-all"
                  />
                </div>

                {/* Hospital picker — only for patient role, and only when there's an actual choice */}
                {selectedRole === 'patient' && hospitals.length > 1 && (
                  <div className="space-y-1.5">
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      Hospital
                    </label>
                    <select
                      value={selectedHospitalId}
                      onChange={(e) => setSelectedHospitalId(e.target.value)}
                      className="w-full px-3.5 py-3 bg-slate-50/70 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white dark:focus:bg-slate-800 text-sm font-medium transition-all"
                    >
                      <option value="">Select your hospital…</option>
                      {hospitals.map((h) => (
                        <option key={h.id} value={h.id}>
                          {h.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Hospital name — only for hospital role */}
                {selectedRole === 'hospital' && (
                  <div className="space-y-1.5">
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      Hospital Name
                    </label>
                    <input
                      type="text"
                      value={hospitalName}
                      onChange={(e) => setHospitalName(e.target.value)}
                      placeholder="e.g. City General Hospital"
                      className="w-full px-3.5 py-3 bg-slate-50/70 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white dark:focus:bg-slate-800 text-sm placeholder-slate-400 dark:placeholder-slate-500 font-medium transition-all"
                    />
                  </div>
                )}

                {/* Email */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Email
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      placeholder="name@domain.com"
                      className="w-full pl-10 pr-4 py-3 bg-slate-50/70 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white dark:focus:bg-slate-800 text-sm placeholder-slate-400 dark:placeholder-slate-500 font-medium transition-all"
                    />
                  </div>
                </div>

                {/* Password */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Password
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      placeholder="Choose a password"
                      className="w-full pl-10 pr-10 py-3 bg-slate-50/70 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white dark:focus:bg-slate-800 text-sm placeholder-slate-400 dark:placeholder-slate-500 font-medium transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={loading}
                  isLoading={loading}
                  className="w-full bg-[#059669] hover:bg-[#047857] text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-emerald-500/25 text-sm flex items-center justify-center gap-2 mt-2"
                >
                  <span>Create Account</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </form>
            )}

            {/* Mode toggle */}
            <div className="text-center pt-1">
              {mode === 'login' ? (
                <button
                  type="button"
                  onClick={() => switchMode('signup')}
                  className="text-sm font-semibold text-sky-600 dark:text-sky-400 hover:text-sky-700 dark:hover:text-sky-300 transition-colors"
                >
                  Don't have an account? <span className="underline">Sign Up</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => switchMode('login')}
                  className="text-sm font-semibold text-sky-600 dark:text-sky-400 hover:text-sky-700 dark:hover:text-sky-300 transition-colors"
                >
                  Already have an account? <span className="underline">Sign In</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Footer Text */}
        <div className="pt-6 text-right">
          <div className="inline-flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500 font-medium">
            <Sprout className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-500" />
            <span>Building healthier rural communities</span>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Login;
