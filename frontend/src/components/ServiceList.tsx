import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import type { Service, TimeRange } from '../types/service';
import ServiceChart from './ServiceChart';
import { Dialog, Transition } from '@headlessui/react'
import { Fragment } from 'react'
import { ExclamationTriangleIcon, BellIcon, BellSlashIcon } from '@heroicons/react/24/outline'
import { fetchWithAuth } from '../utils/api';
import { authService } from '../services/auth';
import NotificationModal from './NotificationModal';
import { parseISO } from 'date-fns';

interface ApiService {
  id: string;
  name: string;
  url: string;
  refresh_frequency: string;
  notification_preferences?: {
    webhook_url: string;
    alert_frequency: 'daily' | 'always';
  } | null;
}

export default function ServiceList() {
  const [services, setServices] = useState<ApiService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedService, setSelectedService] = useState<ApiService | null>(null);
  const [timeRange, setTimeRange] = useState<TimeRange>('1h');
  const [serviceToDelete, setServiceToDelete] = useState<ApiService | null>(null);
  const [notificationModalOpen, setNotificationModalOpen] = useState(false);
  const [selectedServiceForNotification, setSelectedServiceForNotification] = useState<ApiService | null>(null);
  const [isEditingNotification, setIsEditingNotification] = useState(false);

  const fetchServices = async () => {
    try {
      const response = await fetchWithAuth(`${import.meta.env.PUBLIC_API_URL}/services/`);
      if (!response.ok) throw new Error('Failed to fetch services');
      const data = await response.json();
      setServices(data);
      if (!selectedService && data.length > 0) {
        setSelectedService(data[0]);
      }
    } catch (err) {
      setError('Failed to load services');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      window.location.href = '/login';
      return;
    }
    fetchServices();
  }, []);

  useEffect(() => {
    const handleRefresh = () => {
      console.log('Refreshing services...');
      fetchServices();
    };

    document.addEventListener('refreshServices', handleRefresh);

    return () => {
      document.removeEventListener('refreshServices', handleRefresh);
    };
  }, []);

  const handleDeleteClick = (service: ApiService, e: React.MouseEvent) => {
    e.stopPropagation();
    setServiceToDelete(service);
  };

  const handleDeleteConfirm = async () => {
    if (!serviceToDelete) return;

    try {
      const response = await fetchWithAuth(`${import.meta.env.PUBLIC_API_URL}/services/${serviceToDelete.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete service');
      }

      // Refresh the services list
      fetchServices();
      
      // Dispatch event to refresh other components
      document.dispatchEvent(new CustomEvent('refreshServices'));
    } catch (err) {
      console.error('Error deleting service:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete service');
    } finally {
      setServiceToDelete(null);
    }
  };

  const handleAddNotification = async (data: NotificationFormData) => {
    if (!selectedServiceForNotification) return;

    try {
      const response = await fetchWithAuth(
        `${import.meta.env.PUBLIC_API_URL}/services/${selectedServiceForNotification.id}/notifications`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            service_id: selectedServiceForNotification.id,
            webhook_url: data.webhook_url,
            alert_frequency: data.alert_frequency,
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to add notification');
      
      fetchServices(); // Actualiser la liste des services
      setNotificationModalOpen(false);
    } catch (error) {
      console.error('Error adding notification:', error);
    }
  };

  const handleEditNotification = async (data: NotificationFormData) => {
    if (!selectedServiceForNotification) return;

    try {
      const response = await fetchWithAuth(
        `${import.meta.env.PUBLIC_API_URL}/services/${selectedServiceForNotification.id}/notifications`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            service_id: selectedServiceForNotification.id,
            webhook_url: data.webhook_url,
            alert_frequency: data.alert_frequency,
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to update notification');
      
      fetchServices();
      setNotificationModalOpen(false);
    } catch (error) {
      console.error('Error updating notification:', error);
    }
  };

  const handleDeleteNotification = async (serviceId: string) => {
    try {
      const response = await fetchWithAuth(
        `${import.meta.env.PUBLIC_API_URL}/services/${serviceId}/notifications`,
        {
          method: 'DELETE',
        }
      );

      if (!response.ok) throw new Error('Failed to delete notification');
      
      fetchServices();
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }

  if (services.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-gray-500 text-center">No services available</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-4">
        <p className="text-sm text-gray-500">
          Browser Timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Service
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Response Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Check
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Notifications
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {services.map((service) => (
                <tr 
                  key={service.id}
                  onClick={() => setSelectedService(service)}
                  className="cursor-pointer hover:bg-gray-50"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{service.name}</div>
                    <a 
                      href={service.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
                    >
                      {service.url}
                    </a>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      service.stats?.[0]?.status
                        ? 'bg-green-100 text-green-800'
                        : service.stats === null || service.stats.length === 0
                        ? 'bg-gray-100 text-gray-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {service.stats?.[0]?.status ? 'UP' : service.stats === null || service.stats.length === 0 ? 'NO DATA' : 'DOWN'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {service.stats?.[0]?.response_time 
                      ? `${service.stats[0].response_time}ms`
                      : '-'
                    }
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {service.stats?.[0]?.ping_date
                      ? format(
                          parseISO(service.stats[0].ping_date + 'Z'),
                          'PPp',
                          { timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone }
                        )
                      : '-'
                    }
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button 
                      onClick={(e) => handleDeleteClick(service, e)} 
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {service.notification_preferences ? (
                      <div className="flex items-center">
                        <BellIcon className="h-5 w-5 text-green-500 mr-2" />
                        <button
                          onClick={() => {
                            setSelectedServiceForNotification(service);
                            setIsEditingNotification(true);
                            setNotificationModalOpen(true);
                          }}
                          className="text-primary-600 hover:text-primary-900 text-sm"
                        >
                          Edit Settings
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => {
                          setSelectedServiceForNotification(service);
                          setIsEditingNotification(false);
                          setNotificationModalOpen(true);
                        }}
                        className="inline-flex items-center text-primary-600 hover:text-primary-900"
                      >
                        <BellSlashIcon className="h-5 w-5 mr-1" />
                        Add Notification
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedService && (
        <ServiceChart
          service={selectedService}
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange}
        />
      )}

      {/* Delete Confirmation Modal */}
      <Transition.Root show={serviceToDelete !== null} as={Fragment}>
        <Dialog as="div" className="relative z-10" onClose={() => setServiceToDelete(null)}>
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

          <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
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
                <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                  <div className="sm:flex sm:items-start">
                    <div className="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                      <ExclamationTriangleIcon className="h-6 w-6 text-red-600" aria-hidden="true" />
                    </div>
                    <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                      <Dialog.Title as="h3" className="text-base font-semibold leading-6 text-gray-900">
                        Delete Service
                      </Dialog.Title>
                      <div className="mt-2">
                        <p className="text-sm text-gray-500">
                          Are you sure you want to delete "{serviceToDelete?.name}"? This action cannot be undone.
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                    <button
                      type="button"
                      className="inline-flex w-full justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 sm:ml-3 sm:w-auto"
                      onClick={handleDeleteConfirm}
                    >
                      Delete
                    </button>
                    <button
                      type="button"
                      className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                      onClick={() => setServiceToDelete(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition.Root>

      <NotificationModal
        isOpen={notificationModalOpen}
        onClose={() => {
          setNotificationModalOpen(false);
          setSelectedServiceForNotification(null);
          setIsEditingNotification(false);
        }}
        onSubmit={isEditingNotification ? handleEditNotification : handleAddNotification}
        onDelete={isEditingNotification ? () => handleDeleteNotification(selectedServiceForNotification?.id) : undefined}
        initialData={
          selectedServiceForNotification?.notification_preferences ? {
            webhook_url: selectedServiceForNotification.notification_preferences.webhook_url,
            alert_frequency: selectedServiceForNotification.notification_preferences.alert_frequency.toLowerCase() as 'daily' | 'always'
          } : undefined
        }
        title={isEditingNotification ? 'Notification Settings' : 'Add Notification'}
      />
    </div>
  );
}