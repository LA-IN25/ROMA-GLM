'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { apiClient } from '@/lib/api';
import { SolveRequest } from '@/types/api';

interface QuickTaskFormProps {
  onSubmit: () => void;
}

export default function QuickTaskForm({ onSubmit }: QuickTaskFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<SolveRequest>();

  const onFormSubmit = async (data: SolveRequest) => {
    setIsSubmitting(true);
    try {
      await apiClient.createExecution(data);
      reset();
      onSubmit();
    } catch (error) {
      console.error('Failed to create execution:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
      <div>
        <label htmlFor="goal" className="block text-sm font-medium text-gray-700">
          Task Goal
        </label>
        <textarea
          id="goal"
          rows={3}
          className={`mt-1 block w-full ${errors.goal ? 'border-red-300' : 'border-gray-300'} rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm`}
          placeholder="Describe what you want the agent to accomplish..."
          {...register('goal', { 
            required: 'Task goal is required',
            minLength: {
              value: 10,
              message: 'Task goal must be at least 10 characters'
            }
          })}
        />
        {errors.goal && (
          <p className="mt-1 text-sm text-red-600">{errors.goal.message}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="max_depth" className="block text-sm font-medium text-gray-700">
            Max Depth
          </label>
          <select
            id="max_depth"
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            {...register('max_depth', { valueAsNumber: true })}
            defaultValue={2}
          >
            <option value={1}>1 (Simple)</option>
            <option value={2}>2 (Moderate)</option>
            <option value={3}>3 (Complex)</option>
            <option value={4}>4 (Very Complex)</option>
            <option value={5}>5 (Expert)</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Higher values allow more complex task decomposition
          </p>
        </div>

        <div>
          <label htmlFor="config_profile" className="block text-sm font-medium text-gray-700">
            Configuration Profile
          </label>
          <select
            id="config_profile"
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            {...register('config_profile')}
            defaultValue="general"
          >
            <option value="">Default</option>
            <option value="general">General Purpose</option>
            <option value="crypto_agent">Crypto Agent</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Pre-configured agent settings for specific domains
          </p>
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={() => {
            reset();
            onSubmit();
          }}
          className="btn btn-outline"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="btn btn-primary disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Starting...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Start Task
            </>
          )}
        </button>
      </div>
    </form>
  );
}