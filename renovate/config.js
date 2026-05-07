module.exports = {
  platform: 'gitea',
  endpoint: 'https://git.local.example.home/api/v1',
  autodiscover: true,
  autodiscoverFilter: ['john/*'],
  gitAuthor: 'Renovate Bot <renovate@example.home>',
  onboarding: true,
  onboardingConfig: {
    extends: ['config:recommended'],
  },
  packageRules: [
    {
      matchDatasources: ['docker'],
      enabled: true,
    },
  ],
  docker: {
    enabled: true,
  },
  'docker-compose': {
    enabled: true,
  },
};
