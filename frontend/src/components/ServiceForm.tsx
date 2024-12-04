import React from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

const serviceSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  type: z.enum(['API', 'Landing Page', 'Server']),
  url: z.string().url('Invalid URL'),
  checkFrequency: z.enum(['1', '5', '10'])
});

type ServiceFormData = z.infer<typeof serviceSchema>;

export default function ServiceForm() {
  const { register, handleSubmit, formState: { errors }, reset } = useForm<ServiceFormData>();

  const onSubmit = async (data: ServiceFormData) => {
    try {
      // Simulate API call
      console.log('Submitting service:', data);
      reset();
    } catch (error) {
      console.error('Error adding service:', error);
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
          <label className="block text-sm font-medium text-gray-700">Service Type</label>
          <select
            {...register('type')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          >
            <option value="API">API</option>
            <option value="Landing Page">Landing Page</option>
            <option value="Server">Server</option>
          </select>
          {errors.type && (
            <p className="mt-1 text-sm text-red-600">{errors.type.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">URL</label>
          <input
            type="url"
            {...register('url')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          />
          {errors.url && (
            <p className="mt-1 text-sm text-red-600">{errors.url.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Check Frequency (minutes)</label>
          <select
            {...register('checkFrequency')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          >
            <option value="1">Every minute</option>
            <option value="5">Every 5 minutes</option>
            <option value="10">Every 10 minutes</option>
          </select>
          {errors.checkFrequency && (
            <p className="mt-1 text-sm text-red-600">{errors.checkFrequency.message}</p>
          )}
        </div>

        <button
          type="submit"
          className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          Add Service
        </button>
      </div>
    </form>
  );
}