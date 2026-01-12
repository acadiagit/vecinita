/**
 * Feature Flag Configuration
 * Supports gradual rollout, canary testing, and A/B testing
 */

export type FeatureFlagValue = boolean | 'canary' | 'percentage';

export interface FeatureFlags {
  [key: string]: FeatureFlagValue;
}

/**
 * Feature flag keys
 */
export const FEATURE_FLAGS = {
  /**
   * Enable new TypeScript frontend (v2)
   * - false: Use old JavaScript frontend (v1)
   * - true: Use new TypeScript frontend (v2)
   * - 'canary': Enable for canary users
   * - 'percentage': Enable for X% of users (set CANARY_PERCENTAGE)
   */
  NEW_FRONTEND: 'new_frontend',

  /**
   * Enable streaming responses
   * - false: Show complete responses only
   * - true: Show streaming/incremental responses as they arrive
   */
  STREAMING_RESPONSES: 'streaming_responses',

  /**
   * Enable provider/model selection UI
   * - false: Use default provider/model
   * - true: Allow user to select provider and model
   */
  PROVIDER_SELECTION: 'provider_selection',

  /**
   * Enable experimental features
   * - false: Stable features only
   * - true: Include experimental/beta features
   */
  EXPERIMENTAL_FEATURES: 'experimental_features',
} as const;

/**
 * Get feature flag value from multiple sources (in order of precedence):
 * 1. URL query parameter (?feature_flag_key=true)
 * 2. localStorage (persisted user preference)
 * 3. Backend config (from /config endpoint)
 * 4. Default value
 */
export const getFeatureFlag = (
  key: string,
  defaultValue: FeatureFlagValue = true
): FeatureFlagValue => {
  // 1. Check URL query parameter
  const params = new URLSearchParams(window.location.search);
  const queryParam = params.get(key);
  if (queryParam !== null) {
    return queryParam === 'true';
  }

  // 2. Check localStorage
  const storageKey = `feature_flag_${key}`;
  const storedValue = localStorage.getItem(storageKey);
  if (storedValue !== null) {
    return storedValue === 'true';
  }

  // 3. Return default
  return defaultValue;
};

/**
 * Set feature flag in localStorage (user preference)
 */
export const setFeatureFlag = (key: string, value: FeatureFlagValue): void => {
  const storageKey = `feature_flag_${key}`;
  localStorage.setItem(storageKey, String(value));
};

/**
 * Check if user is a canary tester based on localStorage identifier
 */
export const isCanaryUser = (): boolean => {
  const canaryId = localStorage.getItem('canary_user_id');
  if (!canaryId) {
    // Randomly assign new users as canary testers (default 10%)
    const isCanary = Math.random() < 0.1;
    if (isCanary) {
      localStorage.setItem('canary_user_id', `canary_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    }
    return isCanary;
  }
  return true;
};

/**
 * Check if user should see feature based on percentage rollout
 * @param percentage Number 0-100 indicating percentage of users to show feature to
 */
export const shouldShowFeatureByPercentage = (percentage: number = 10): boolean => {
  const userId = localStorage.getItem('user_id') || `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  localStorage.setItem('user_id', userId);
  
  // Use deterministic hash based on user ID for consistent rollout
  const hash = userId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return (hash % 100) < percentage;
};

/**
 * Evaluate feature flag with all logic:
 * - Direct true/false
 * - 'canary': only for canary users
 * - 'percentage': X% of users (using CANARY_PERCENTAGE env var or default 10%)
 */
export const evaluateFeatureFlag = (
  value: FeatureFlagValue,
  canaryPercentage: number = 10
): boolean => {
  if (typeof value === 'boolean') {
    return value;
  }
  
  if (value === 'canary') {
    return isCanaryUser();
  }
  
  if (value === 'percentage') {
    return shouldShowFeatureByPercentage(canaryPercentage);
  }
  
  return false;
};

/**
 * Default feature flag configuration
 * Customize based on rollout strategy
 */
export const DEFAULT_FEATURE_FLAGS: FeatureFlags = {
  /**
   * Gradual rollout strategy:
   * Week 1-2: 'canary' - only canary testers
   * Week 3-4: 'percentage' with 25% - 25% of users
   * Week 5-6: 'percentage' with 50% - 50% of users
   * Week 7+: true - all users
   */
  [FEATURE_FLAGS.NEW_FRONTEND]: true, // Fully rolled out

  /**
   * Streaming enabled by default (SSE support)
   */
  [FEATURE_FLAGS.STREAMING_RESPONSES]: true,

  /**
   * Provider selection enabled by default
   */
  [FEATURE_FLAGS.PROVIDER_SELECTION]: true,

  /**
   * Experimental features disabled by default
   */
  [FEATURE_FLAGS.EXPERIMENTAL_FEATURES]: 'canary', // Canary users only
};

/**
 * Log feature flag state for debugging
 */
export const logFeatureFlags = (): void => {
  if (import.meta.env.VITE_DEBUG === 'true') {
    console.group('Feature Flags');
    Object.entries(FEATURE_FLAGS).forEach(([name, key]) => {
      const value = getFeatureFlag(key, DEFAULT_FEATURE_FLAGS[key]);
      const evaluated = evaluateFeatureFlag(value);
      console.log(`${name} (${key}): ${value} -> ${evaluated}`);
    });
    console.groupEnd();
  }
};
