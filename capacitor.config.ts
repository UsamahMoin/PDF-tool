import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.usamahmoin.pdftool',
  appName: 'PDF Tool',
  webDir: 'dist',
  ios: {
    contentInset: 'always',
  },
  android: {
    allowMixedContent: false,
  },
  plugins: {
    Camera: {
      permissions: ['camera', 'photos'],
    },
  },
}

export default config
