import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Building,
  User as UserIcon,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  Cpu,
  BarChart3,
  Leaf,
  AlertCircle,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { registerUser } from '../services/api';
import bgImage from '../assets/cnc_login_bg.jpg';
import logoImage from '../assets/logo.png';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Login form state
  const [loginData, setLoginData] = useState({
    company_name: '',
    username: '',
    password: '',
  });

  // Register form state (6 precise fields)
  const [registerData, setRegisterData] = useState({
    company_name: '',
    admin_name: '',
    email: '',
    username: '',
    password: '',
    confirm_password: '',
  });

  // Common email typo domains detection dictionary
  const TYPO_DOMAINS: Record<string, string> = {
    'gamil.com': 'gmail.com',
    'gmial.com': 'gmail.com',
    'gmai.com': 'gmail.com',
    'gmaill.com': 'gmail.com',
    'gmil.com': 'gmail.com',
    'gmaik.com': 'gmail.com',
    'yaho.com': 'yahoo.com',
    'yahooo.com': 'yahoo.com',
    'hotmial.com': 'hotmail.com',
    'hotmale.com': 'hotmail.com',
    'outlok.com': 'outlook.com',
    'outloo.com': 'outlook.com',
    'redifmail.com': 'rediffmail.com',
  };

  const emailDomain = registerData.email.includes('@') ? registerData.email.split('@')[1]?.toLowerCase().trim() : '';
  const emailTypoSuggestion = emailDomain ? TYPO_DOMAINS[emailDomain] : undefined;

  const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$/;
  const isEmailValid = emailRegex.test(registerData.email.trim()) && !emailTypoSuggestion;

  const pwd = registerData.password;
  const hasMinLength = pwd.length >= 8;
  const hasUpper = /[A-Z]/.test(pwd);
  const hasLower = /[a-z]/.test(pwd);
  const hasDigit = /\d/.test(pwd);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>\-_=+/\\\[\]`~]/.test(pwd);
  const isPasswordValid = hasMinLength && hasUpper && hasLower && hasDigit && hasSpecial;
  const isConfirmMatch = registerData.confirm_password.length > 0 && registerData.password === registerData.confirm_password;

  const handleFixEmailTypo = () => {
    if (emailTypoSuggestion && registerData.email.includes('@')) {
      const usernamePart = registerData.email.split('@')[0];
      setRegisterData({
        ...registerData,
        email: `${usernamePart}@${emailTypoSuggestion}`,
      });
      setError('');
    }
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginData.username.trim() || !loginData.password) {
      setError('Please fill in both username and password.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await login({
        company_name: loginData.company_name.trim() || undefined,
        username: loginData.username.trim(),
        password: loginData.password,
      });
      navigate('/', { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !registerData.company_name.trim() ||
      !registerData.admin_name.trim() ||
      !registerData.email.trim() ||
      !registerData.username.trim() ||
      !registerData.password ||
      !registerData.confirm_password
    ) {
      setError('Please fill in all required fields.');
      return;
    }
    if (emailTypoSuggestion) {
      setError(`Invalid email domain '${emailDomain}'. Did you mean '@${emailTypoSuggestion}'?`);
      return;
    }
    if (!isEmailValid) {
      setError('Please enter a valid email address with a complete domain (e.g. user@company.com).');
      return;
    }
    if (!isPasswordValid) {
      setError('Password does not satisfy complexity requirements (Min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special character).');
      return;
    }
    if (registerData.password !== registerData.confirm_password) {
      setError('Passwords do not match. Please ensure Password and Confirm Password are identical.');
      return;
    }

    setError('');
    setLoading(true);
    try {
      await registerUser({
        company_name: registerData.company_name.trim(),
        admin_name: registerData.admin_name.trim(),
        email: registerData.email.trim().toLowerCase(),
        username: registerData.username.trim(),
        password: registerData.password,
        role: 'Administrator',
      });

      // Pre-fill login form with newly registered account details
      setLoginData({
        company_name: registerData.company_name.trim(),
        username: registerData.username.trim(),
        password: '',
      });

      // Reset register form
      setRegisterData({
        company_name: '',
        admin_name: '',
        email: '',
        username: '',
        password: '',
        confirm_password: '',
      });

      setSuccessMsg('Account created successfully! Please sign in with your password to access the fleet.');
      setMode('login');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(' | '));
      } else {
        setError(detail || 'Registration failed. Username or email may already exist.');
      }
    } finally {
      setLoading(false);
    }
  };

  const features = [
    { icon: Cpu, title: 'Predict', subtitle: 'Failures Early' },
    { icon: BarChart3, title: 'Reduce', subtitle: 'Downtime' },
    { icon: ShieldCheck, title: 'Increase', subtitle: 'Productivity' },
    { icon: Leaf, title: 'Sustainable', subtitle: 'Operations' },
  ];

  return (
    <div className="min-h-screen relative flex items-center justify-center p-4 sm:p-6 lg:p-8 overflow-hidden select-none bg-slate-950 font-sans">
      {/* Background Image with Dark Vignette & Industrial Overlay */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat transition-transform duration-1000 scale-105"
        style={{ backgroundImage: `url(${bgImage})` }}
      />
      <div className="absolute inset-0 bg-gradient-to-r from-slate-950/95 via-slate-950/80 to-slate-950/95 backdrop-blur-[2px]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/15 via-slate-950/60 to-slate-950/95" />

      {/* Main Container Layout */}
      <div className="relative z-10 w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">

        {/* Left Side Features (visible on lg screens) */}
        <div className="hidden lg:flex lg:col-span-3 flex-col justify-between py-6 space-y-12">
          {/* Feature List */}
          <div className="space-y-8">
            {features.map((f, i) => (
              <div key={i} className="flex items-center gap-4 group">
                <div className="h-11 w-11 rounded-xl bg-blue-950/60 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:border-blue-400 group-hover:scale-105 transition-all shadow-lg shadow-blue-950/50">
                  <f.icon className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-white text-xs font-semibold tracking-wide leading-tight">{f.title}</div>
                  <div className="text-slate-400 text-xs tracking-wide leading-tight">{f.subtitle}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Bottom Left Branding */}
          <div className="space-y-1 pt-4 border-t border-slate-800/60">
            <div className="h-0.5 w-7 bg-blue-500 rounded-full mb-3" />
            <div className="text-[10px] font-mono tracking-widest text-slate-400 uppercase">CNC | AI | RELIABILITY</div>
            <div className="text-xs font-mono font-bold tracking-wider text-slate-200">PREDICTCNC</div>
          </div>
        </div>

        {/* Center Main Glass Card */}
        <div className="lg:col-span-6 w-full max-w-lg mx-auto">
          <div className="rounded-3xl border border-blue-500/30 bg-[#070D1F]/90 backdrop-blur-2xl p-6 sm:p-9 shadow-[0_0_60px_-15px_rgba(37,99,235,0.3)] space-y-6">

            {/* Card Header: Logo + Right Badge */}
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-5">
              {/* Brand Logo & Name */}
              <div className="flex items-center gap-3.5">
                <div className="h-14 w-14 flex items-center justify-center shrink-0">
                  <img src={logoImage} alt="PredictCNC Logo" className="h-12 w-12 object-contain drop-shadow-[0_0_12px_rgba(56,189,248,0.4)]" />
                </div>
                <div>
                  <div className="text-2xl font-display font-extrabold tracking-tight text-white flex items-center gap-1">
                    Predict<span className="text-blue-500">CNC</span>
                  </div>
                  <div className="text-[9px] font-mono tracking-widest text-slate-400 uppercase">
                    AI-BASED PREDICTIVE MAINTENANCE
                  </div>
                </div>
              </div>

              {/* Right Tagline */}
              <div className="border-l border-slate-800 pl-4 text-right">
                <div className="text-[9px] font-mono text-slate-400 uppercase tracking-widest leading-relaxed">
                  <div>SMART</div>
                  <div>MACHINES</div>
                  <div>RELIABLE</div>
                  <div className="text-blue-400 font-semibold">TOMORROW</div>
                </div>
              </div>
            </div>

            {/* Mode Switcher Tabs */}
            <div className="grid grid-cols-2 p-1 rounded-xl bg-[#030712]/80 border border-slate-800 text-xs font-mono">
              <button
                type="button"
                onClick={() => {
                  setMode('login');
                  setError('');
                }}
                className={`py-2.5 rounded-lg transition-all text-center ${mode === 'login'
                    ? 'bg-blue-600 text-white font-semibold shadow-lg shadow-blue-600/30'
                    : 'text-slate-400 hover:text-white'
                  }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode('register');
                  setError('');
                  setSuccessMsg('');
                }}
                className={`py-2.5 rounded-lg transition-all text-center ${mode === 'register'
                    ? 'bg-blue-600 text-white font-semibold shadow-lg shadow-blue-600/30'
                    : 'text-slate-400 hover:text-white'
                  }`}
              >
                Register Operator
              </button>
            </div>

            {/* Success Message */}
            {successMsg && mode === 'login' && (
              <div className="flex items-start gap-2.5 p-3.5 rounded-xl border border-emerald-500/40 bg-emerald-950/30 text-emerald-300 text-xs backdrop-blur-sm animate-fade-in">
                <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5 text-emerald-400" />
                <span>{successMsg}</span>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="flex items-start gap-2.5 p-3.5 rounded-xl border border-rose-500/40 bg-rose-950/30 text-rose-300 text-xs backdrop-blur-sm animate-shake">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-rose-400" />
                <span>{error}</span>
              </div>
            )}

            {/* Form Mode 1: Sign In */}
            {mode === 'login' ? (
              <form onSubmit={handleLoginSubmit} className="space-y-4 text-xs">
                {/* Company Name */}
                <div>
                  <label className="block text-slate-300 font-medium mb-1.5">Company Name</label>
                  <div className="relative">
                    <Building className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      placeholder="Enter your company name"
                      value={loginData.company_name}
                      onChange={(e) => setLoginData({ ...loginData, company_name: e.target.value })}
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-800 bg-[#030712]/90 text-white font-mono text-xs placeholder:text-slate-600 focus:border-blue-500 focus:bg-[#030712] focus:outline-none transition-all"
                    />
                  </div>
                </div>

                {/* Username or Email */}
                <div>
                  <label className="block text-slate-300 font-medium mb-1.5">Username or Email *</label>
                  <div className="relative">
                    <UserIcon className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      required
                      placeholder="Enter your username or email"
                      value={loginData.username}
                      onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
                      className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-800 bg-[#030712]/90 text-white font-mono text-xs placeholder:text-slate-600 focus:border-blue-500 focus:bg-[#030712] focus:outline-none transition-all"
                    />
                  </div>
                </div>

                {/* Password with Eye Toggle */}
                <div>
                  <label className="block text-slate-300 font-medium mb-1.5">Password *</label>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      placeholder="Enter your password"
                      value={loginData.password}
                      onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                      className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-slate-800 bg-[#030712]/90 text-white font-mono text-xs placeholder:text-slate-600 focus:border-blue-500 focus:bg-[#030712] focus:outline-none transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-3 text-slate-500 hover:text-slate-300 transition-colors"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* Submit Action Button */}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-600/30 hover:shadow-blue-600/50 mt-2"
                >
                  {loading ? (
                    <>
                      <Activity className="h-4 w-4 animate-spin" />
                      <span>Authenticating Credentials...</span>
                    </>
                  ) : (
                    <>
                      <span>Authenticate & Access Fleet</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </form>
            ) : (
              /* Form Mode 2: Register Operator */
              <form onSubmit={handleRegisterSubmit} className="space-y-3.5 text-xs">
                {/* 1. Company Name */}
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Company Name *</label>
                  <div className="relative">
                    <Building className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      required
                      placeholder="Enter company name"
                      value={registerData.company_name}
                      onChange={(e) => setRegisterData({ ...registerData, company_name: e.target.value })}
                      className="w-full pl-10 pr-3.5 py-2 rounded-xl border border-slate-800 bg-[#030712]/90 text-white font-mono text-xs placeholder:text-slate-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>

                {/* 2. Admin Name & 3. Username */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Admin Name *</label>
                    <input
                      type="text"
                      required
                      placeholder="Enter admin name"
                      value={registerData.admin_name}
                      onChange={(e) => setRegisterData({ ...registerData, admin_name: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl border border-slate-800 bg-[#030712]/90 text-white font-mono text-xs placeholder:text-slate-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Username *</label>
                    <input
                      type="text"
                      required
                      placeholder="Enter username"
                      value={registerData.username}
                      onChange={(e) => setRegisterData({ ...registerData, username: e.target.value })}
                      className="w-full px-3.5 py-2 rounded-xl border border-slate-800 bg-[#030712]/90 text-white font-mono text-xs placeholder:text-slate-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>

                {/* 4. Email with Typo Indicator */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-slate-300 font-medium">Email Address *</label>
                    {registerData.email && (
                      emailTypoSuggestion ? (
                        <button
                          type="button"
                          onClick={handleFixEmailTypo}
                          className="text-[10px] font-mono text-rose-400 hover:underline flex items-center gap-1"
                        >
                          <span>✗ Typo: Use @{emailTypoSuggestion}?</span>
                          <span className="text-[9px] bg-rose-500/20 px-1 rounded text-white font-semibold">Fix</span>
                        </button>
                      ) : (
                        <span className={`text-[10px] font-mono ${isEmailValid ? 'text-emerald-400' : 'text-amber-400'}`}>
                          {isEmailValid ? '✓ Valid Domain' : '⚠ Incomplete domain'}
                        </span>
                      )
                    )}
                  </div>
                  <div className="relative">
                    <input
                      type="email"
                      required
                      placeholder="Enter email address"
                      value={registerData.email}
                      onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                      className={`w-full px-3.5 py-2 rounded-xl border ${registerData.email && emailTypoSuggestion
                          ? 'border-rose-500/60 bg-rose-950/20'
                          : registerData.email && !isEmailValid
                            ? 'border-amber-500/60 bg-amber-950/20'
                            : 'border-slate-800 bg-[#030712]/90'
                        } text-white font-mono text-xs placeholder:text-slate-600 focus:border-blue-500 focus:outline-none`}
                    />
                  </div>
                </div>

                {/* 5. Password & 6. Confirm Password */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Password *</label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        required
                        placeholder="Enter password"
                        value={registerData.password}
                        onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                        className="w-full pl-3.5 pr-8 py-2 rounded-xl border border-slate-800 bg-[#030712]/90 text-white font-mono text-xs placeholder:text-slate-600 focus:border-blue-500 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-2.5 top-2.5 text-slate-500 hover:text-slate-300"
                      >
                        {showPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-slate-300 font-medium">Confirm Pass *</label>
                      {registerData.confirm_password && (
                        <span className={`text-[9px] font-mono ${isConfirmMatch ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {isConfirmMatch ? '✓ Match' : '✗ Differ'}
                        </span>
                      )}
                    </div>
                    <div className="relative">
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        required
                        placeholder="Confirm password"
                        value={registerData.confirm_password}
                        onChange={(e) => setRegisterData({ ...registerData, confirm_password: e.target.value })}
                        className={`w-full pl-3.5 pr-8 py-2 rounded-xl border ${registerData.confirm_password && !isConfirmMatch ? 'border-rose-500/60 bg-rose-950/20' : 'border-slate-800 bg-[#030712]/90'
                          } text-white font-mono text-xs placeholder:text-slate-600 focus:border-blue-500 focus:outline-none`}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-2.5 top-2.5 text-slate-500 hover:text-slate-300"
                      >
                        {showConfirmPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Live Password Complexity Checklist */}
                {registerData.password && (
                  <div className="p-3 rounded-xl border border-slate-800 bg-[#030712]/95 text-[11px] font-mono space-y-1">
                    <div className="text-slate-400 text-[10px] uppercase tracking-wider font-semibold mb-1">
                      Password Requirements:
                    </div>
                    <div className="grid grid-cols-2 gap-1 text-[10px]">
                      <span className={hasMinLength ? 'text-emerald-400' : 'text-slate-500'}>
                        {hasMinLength ? '✓' : '○'} Min 8 characters
                      </span>
                      <span className={hasUpper ? 'text-emerald-400' : 'text-slate-500'}>
                        {hasUpper ? '✓' : '○'} 1 Uppercase (A-Z)
                      </span>
                      <span className={hasLower ? 'text-emerald-400' : 'text-slate-500'}>
                        {hasLower ? '✓' : '○'} 1 Lowercase (a-z)
                      </span>
                      <span className={hasDigit ? 'text-emerald-400' : 'text-slate-500'}>
                        {hasDigit ? '✓' : '○'} 1 Number (0-9)
                      </span>
                      <span className={`col-span-2 ${hasSpecial ? 'text-emerald-400' : 'text-slate-500'}`}>
                        {hasSpecial ? '✓' : '○'} 1 Special Character (@, #, $, %, etc.)
                      </span>
                    </div>
                  </div>
                )}

                {/* Register Submit Button */}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-600/30 hover:shadow-blue-600/50 mt-2"
                >
                  {loading ? (
                    <>
                      <Activity className="h-4 w-4 animate-spin" />
                      <span>Creating Industrial Account...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="h-4 w-4" />
                      <span>Create Industrial Account</span>
                    </>
                  )}
                </button>
              </form>
            )}

            {/* Bottom Security Footer */}
            <div className="flex items-center justify-center gap-2 text-[10px] font-mono text-slate-400 pt-3 border-t border-slate-800/80">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
              <span>256-Bit Encrypted PostgreSQL 18 Subsystem</span>
            </div>

          </div>
        </div>

        {/* Right Side Branding / Tagline (visible on lg screens) */}
        <div className="hidden lg:flex lg:col-span-3 flex-col justify-end items-end py-6 text-right space-y-2">
          <div className="space-y-1">
            <div className="text-[11px] font-mono text-slate-300 font-semibold uppercase tracking-wider">
              PRECISION TODAY.
            </div>
            <div className="text-[10px] font-mono text-slate-400 tracking-wider">
              A SMARTER TOMORROW.
            </div>
          </div>
          <div className="h-0.5 w-8 bg-blue-500 rounded-full" />
        </div>

      </div>
    </div>
  );
};
