import React from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

const notificationSchema = z.object({
  webhook_url: z.string().url('Invalid webhook URL'),
  alert_frequency: z.enum(['daily', 'always'])
});

type NotificationFormData = z.infer<typeof notificationSchema>;

interface NotificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: NotificationFormData) => Promise<void>;
  onDelete?: () => Promise<void>;
  initialData?: {
    webhook_url: string;
    alert_frequency: 'daily' | 'always';
  };
  title: string;
}

export default function NotificationModal({ 
  isOpen, 
  onClose, 
  onSubmit,
  onDelete,
  initialData,
  title 
}: NotificationModalProps) {
  const { register, handleSubmit, formState: { errors }, reset } = useForm<NotificationFormData>({
    defaultValues: initialData
  });

  const handleFormSubmit = async (data: NotificationFormData) => {
    try {
      await onSubmit(data);
      onClose();
      reset();
    } catch (error) {
      console.error('Error submitting notification:', error);
    }
  };

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                <div>
                  <Dialog.Title as="h3" className="text-lg font-semibold leading-6 text-gray-900 mb-4">
                    {title}
                  </Dialog.Title>
                  
                  <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Slack Webhook URL
                      </label>
                      <input
                        type="url"
                        {...register('webhook_url')}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                        placeholder="https://hooks.slack.com/..."
                      />
                      {errors.webhook_url && (
                        <p className="mt-1 text-sm text-red-600">{errors.webhook_url.message}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Alert Frequency
                      </label>
                      <select
                        {...register('alert_frequency')}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                      >
                        <option value="daily">Daily</option>
                        <option value="always">Always</option>
                      </select>
                      {errors.alert_frequency && (
                        <p className="mt-1 text-sm text-red-600">{errors.alert_frequency.message}</p>
                      )}
                    </div>

                    <div className="mt-5 sm:mt-6 flex flex-col space-y-3">
                      <button
                        type="submit"
                        className="inline-flex w-full justify-center rounded-md bg-primary-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                      >
                        Save Changes
                      </button>
                      
                      {onDelete && (
                        <button
                          type="button"
                          onClick={async () => {
                            await onDelete();
                            onClose();
                          }}
                          className="inline-flex w-full justify-center rounded-md bg-red-100 px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-200"
                        >
                          Remove Notification
                        </button>
                      )}

                      <button
                        type="button"
                        className="inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                        onClick={onClose}
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
} 