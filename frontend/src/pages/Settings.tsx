export default function Settings() {
  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      <div className="space-y-6">
        {/* Connectors */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Message Connectors</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-4 border border-gray-200 rounded-lg">
              <div>
                <h3 className="font-medium">SMTP (Email)</h3>
                <p className="text-sm text-gray-500">MailHog - Development</p>
              </div>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                Connected
              </span>
            </div>

            <div className="flex justify-between items-center p-4 border border-gray-200 rounded-lg">
              <div>
                <h3 className="font-medium">Twilio (SMS)</h3>
                <p className="text-sm text-gray-500">Stub - Configure in .env</p>
              </div>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
                Stub
              </span>
            </div>

            <div className="flex justify-between items-center p-4 border border-gray-200 rounded-lg">
              <div>
                <h3 className="font-medium">WhatsApp Business</h3>
                <p className="text-sm text-gray-500">Not configured</p>
              </div>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                Disabled
              </span>
            </div>
          </div>
        </div>

        {/* Security */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Security</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium">Encryption</h3>
                <p className="text-sm text-gray-500">PII data encrypted with AES-256</p>
              </div>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                Enabled
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium">Audit Logging</h3>
                <p className="text-sm text-gray-500">All CUD operations logged</p>
              </div>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                Enabled
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium">Disk Encryption</h3>
                <p className="text-sm text-gray-500">Recommended: LUKS/BitLocker</p>
              </div>
              <a href="#" className="text-primary-600 text-sm">
                Learn More
              </a>
            </div>
          </div>
        </div>

        {/* Backup */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Backup & Restore</h2>
          <p className="text-gray-600 mb-4">
            Use the provided scripts to create encrypted backups:
          </p>
          <div className="bg-gray-50 p-4 rounded-lg font-mono text-sm space-y-2">
            <div>
              <span className="text-gray-500">Backup:</span>
              <code className="ml-2">./scripts/backup.sh backup-$(date +%Y%m%d).sql.gpg</code>
            </div>
            <div>
              <span className="text-gray-500">Restore:</span>
              <code className="ml-2">./scripts/restore.sh backup-20241201.sql.gpg</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
