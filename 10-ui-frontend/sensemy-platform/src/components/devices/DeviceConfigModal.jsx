// src/components/devices/DeviceConfigModal.jsx
import Modal from '../common/Modal.jsx';
import StatusBadge from '../common/StatusBadge.jsx';
import { getRequiredAction } from '../../utils/deviceStatus.js';

const DeviceConfigModal = ({ device, onClose }) => {
  const requiredAction = getRequiredAction(device);

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={`Configure Device: ${device.deveui}`}
      size="large"
    >
      <div className="space-y-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-3">Device Information</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700">DevEUI</label>
              <div className="text-sm text-gray-900 font-mono">{device.deveui}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Name</label>
              <div className="text-sm text-gray-900">{device.name || 'Unnamed Device'}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Current Status</label>
              <div className="mt-1">
                <StatusBadge device={device} size="small" />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Required Action</label>
              <div className="text-sm text-gray-900">{requiredAction}</div>
            </div>
          </div>
        </div>

        {device.metadata_hints && (
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">💡 Metadata Hints</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {device.metadata_hints.device_model && (
                <div>
                  <span className="font-medium">Device Model:</span> {device.metadata_hints.device_model}
                </div>
              )}
              {device.metadata_hints.device_vendor && (
                <div>
                  <span className="font-medium">Vendor:</span> {device.metadata_hints.device_vendor}
                </div>
              )}
              {device.metadata_hints.sensor_type && (
                <div>
                  <span className="font-medium">Sensor Type:</span> {device.metadata_hints.sensor_type}
                </div>
              )}
              {device.metadata_hints.source && (
                <div>
                  <span className="font-medium">Source:</span> {device.metadata_hints.source}
                </div>
              )}
            </div>
          </div>
        )}

        <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
          <div className="text-center">
            <div className="text-4xl mb-2">🚧</div>
            <h4 className="font-medium text-gray-900 mb-1">Configuration Form</h4>
            <p className="text-sm text-gray-600">
              Device type selection and location assignment form will be implemented next.
            </p>
          </div>
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            disabled={true}
            className="px-4 py-2 bg-blue-600 text-white rounded-md opacity-50 cursor-not-allowed"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default DeviceConfigModal;
