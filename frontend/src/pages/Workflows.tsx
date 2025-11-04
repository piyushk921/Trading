export default function Workflows() {
  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Workflows</h1>
        <button className="btn btn-primary">Create Workflow</button>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Automation Engine</h2>
        <p className="text-gray-600 mb-4">
          Workflows allow you to automate repetitive tasks based on triggers and actions.
        </p>

        <div className="space-y-4">
          {/* Example Workflow */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-medium">Welcome Email on Onboarding</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Automatically send welcome email when client is onboarded
                </p>
              </div>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                Active
              </span>
            </div>

            <div className="mt-4 text-sm">
              <div className="flex items-center text-gray-600">
                <span className="font-medium mr-2">Trigger:</span>
                <code className="bg-gray-100 px-2 py-1 rounded">client.onboarded</code>
              </div>
              <div className="flex items-center text-gray-600 mt-2">
                <span className="font-medium mr-2">Action:</span>
                <code className="bg-gray-100 px-2 py-1 rounded">send_email</code>
              </div>
            </div>
          </div>

          {/* Workflow UI Stub */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <p className="text-gray-500">
              Workflow builder UI coming soon. Configure workflows in the database or via API.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
