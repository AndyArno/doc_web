import apiClient from './index'

export interface SetupStatus {
  initialized: boolean
}

export function getSetupStatus(): Promise<SetupStatus> {
  return apiClient.get('/setup/status')
}
