import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';
import { Client, Message, Task } from '../types';

export default function ClientDetail() {
  const { id } = useParams<{ id: string }>();
  const [client, setClient] = useState<Client | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'messages' | 'tasks'>('overview');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchClientData();
    }
  }, [id]);

  const fetchClientData = async () => {
    try {
      const [clientRes, messagesRes, tasksRes] = await Promise.allSettled([
        api.get<Client>(`/clients/${id}`),
        api.get<Message[]>(`/messages?clientId=${id}`),
        api.get<Task[]>(`/tasks?clientId=${id}`),
      ]);

      if (clientRes.status === 'fulfilled') {
        setClient(clientRes.value.data);
      }
      if (messagesRes.status === 'fulfilled') {
        setMessages(messagesRes.value.data || []);
      }
      if (tasksRes.status === 'fulfilled') {
        setTasks(tasksRes.value.data || []);
      }
    } catch (error) {
      console.error('Failed to fetch client data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="p-4">Loading...</div>;
  }

  if (!client) {
    return <div className="p-4">Client not found</div>;
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {client.firstName} {client.lastName}
        </h1>
        <p className="text-gray-500">{client.email}</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {['overview', 'messages', 'tasks'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`${
                activeTab === tab
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm capitalize`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Contact Information</h3>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-500">Email</dt>
                <dd className="text-sm font-medium">{client.email}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Phone</dt>
                <dd className="text-sm font-medium">{client.phone || '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Status</dt>
                <dd className="text-sm font-medium capitalize">{client.status}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Risk Profile</dt>
                <dd className="text-sm font-medium capitalize">{client.riskProfile || '-'}</dd>
              </div>
            </dl>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Account Details</h3>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-500">Onboarded</dt>
                <dd className="text-sm font-medium">{client.isOnboarded ? 'Yes' : 'No'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Created</dt>
                <dd className="text-sm font-medium">
                  {new Date(client.createdAt).toLocaleDateString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Assigned RM</dt>
                <dd className="text-sm font-medium">
                  {client.assignedRm
                    ? `${client.assignedRm.firstName} ${client.assignedRm.lastName}`
                    : '-'}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      )}

      {activeTab === 'messages' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Messages</h3>
          {messages.length === 0 ? (
            <p className="text-gray-500">No messages yet.</p>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <div key={message.id} className="border-b pb-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs text-gray-500 uppercase">{message.channel}</span>
                      <h4 className="font-medium">{message.subject || 'No subject'}</h4>
                      <p className="text-sm text-gray-600 mt-1">{message.body}</p>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(message.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'tasks' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Tasks</h3>
          {tasks.length === 0 ? (
            <p className="text-gray-500">No tasks yet.</p>
          ) : (
            <div className="space-y-4">
              {tasks.map((task) => (
                <div key={task.id} className="border-b pb-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium">{task.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                      <span className="text-xs text-gray-500 capitalize">{task.status}</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {task.dueDate ? new Date(task.dueDate).toLocaleDateString() : 'No due date'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
