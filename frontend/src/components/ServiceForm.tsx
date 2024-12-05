import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import type { components } from '../types/api';
import { fetchWithAuth } from '../utils/api';

type RefreshFrequency = components['schemas']['RefreshFrequency'];

const serviceSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  url: z.string().url('Invalid URL'),
  refresh_frequency: z.enum(['1 minute', '10 minutes', '1 hour'] as const)
});

type ServiceFormData = z.infer<typeof serviceSchema>;

interface ServiceFormProps {
  onSuccess?: () => void;
}

export default function ServiceForm({ onSuccess }: ServiceFormProps) {
  const { register, handleSubmit, formState: { errors }, reset } = useForm<ServiceFormData>();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const onSubmit = async (data: ServiceFormData) => {
    setIsSubmitting(true);
    setSubmitStatus('idle');

    try {
      const response = await fetchWithAuth(`${import.meta.env.PUBLIC_API_URL}/services/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: data.name,
          url: data.url,
          refresh_frequency: data.refresh_frequency
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create service');
      }

      const result = await response.json();
      setSubmitStatus('success');
      reset();
      
      document.dispatchEvent(new CustomEvent('refreshServices'));
      
      setTimeout(() => setSubmitStatus('idle'), 3000);

    } catch (error) {
      console.error('Error creating service:', error);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="bg-white p-6 rounded-lg shadow-sm">
      <h2 className="text-xl font-semibold mb-4">Add New Service</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Service Name</label>
          <input
            type="text"
            {...register('name')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">URL</label>
          <input
            type="url"
            {...register('url')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            placeholder="https://example.com"
          />
          {errors.url && (
            <p className="mt-1 text-sm text-red-600">{errors.url.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Check Frequency</label>
          <select
            {...register('refresh_frequency')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          >
            <option value="1 minute">Every minute</option>
            <option value="10 minutes">Every 10 minutes</option>
            <option value="1 hour">Every hour</option>
          </select>
          {errors.refresh_frequency && (
            <p className="mt-1 text-sm text-red-600">{errors.refresh_frequency.message}</p>
          )}
        </div>

        {submitStatus === 'success' && (
          <div className="p-3 bg-green-100 text-green-700 rounded-md">
            Service added successfully!
          </div>
        )}
        
        {submitStatus === 'error' && (
          <div className="p-3 bg-red-100 text-red-700 rounded-md">
            Failed to add service. Please try again.
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className={`w-full py-2 px-4 rounded-md text-white
            ${isSubmitting 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-primary-600 hover:bg-primary-700'}
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2`}
        >
          {isSubmitting ? 'Adding Service...' : 'Add Service'}
        </button>
      </div>
    </form>
  );
}