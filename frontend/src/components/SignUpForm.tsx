import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { authService } from '../services/auth';
import type { SignUpCredentials } from '../services/auth';

export default function SignUpForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<SignUpCredentials>();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [countdown, setCountdown] = useState(3);

  const onSubmit = async (data: SignUpCredentials) => {
    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      await authService.signUp(data);
      setSuccess(true);
      
      // Start countdown
      let count = 3;
      setCountdown(count);
      
      const timer = setInterval(() => {
        count -= 1;
        setCountdown(count);
        
        if (count === 0) {
          clearInterval(timer);
          window.location.href = '/login?registered=true';
        }
      }, 1000);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign up failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" method="POST">
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          {...register('username', { required: 'Email address is required' })}
          type="email"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          disabled={success}
        />
        {errors.username && (
          <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Password
        </label>
        <input
          {...register('password', { 
            required: 'Password is required',
            minLength: {
              value: 8,
              message: 'Password must be at least 8 characters'
            }
          })}
          type="password"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          disabled={success}
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {success && (
        <div className="rounded-md bg-green-50 p-4">
          <p className="text-sm text-green-700">
            Account created successfully! Redirecting in {countdown} seconds...
          </p>
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading || success}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Creating account...' : 'Sign up'}
      </button>
    </form>
  );
} 