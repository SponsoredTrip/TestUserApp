import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Image,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { colors, layout, spacing, typography, shadows, radius, brand } from '../constants/theme';
import { Card } from '../components/UI/Card';
import { Button } from '../components/UI/Button';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
}

export default function Index() {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    full_name: '',
  });

  useEffect(() => {
    checkExistingAuth();
  }, []);

  const checkExistingAuth = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (token) {
        // Verify token with backend
        const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        if (response.ok) {
          router.replace('/home');
          return;
        } else {
          await AsyncStorage.removeItem('auth_token');
        }
      }
    } catch (error) {
      console.error('Auth check error:', error);
    } finally {
      setCheckingAuth(false);
    }
  };

  const handleAuth = async () => {
    if (!formData.username || !formData.password) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    if (!isLogin && (!formData.email || !formData.full_name)) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const body = isLogin 
        ? { username: formData.username, password: formData.password }
        : formData;

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (response.ok) {
        await AsyncStorage.setItem('auth_token', data.access_token);
        await AsyncStorage.setItem('user_data', JSON.stringify(data.user));
        router.replace('/home');
      } else {
        Alert.alert('Error', data.detail || 'Authentication failed');
      }
    } catch (error) {
      console.error('Auth error:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleAuthMode = () => {
    setIsLogin(!isLogin);
    setFormData({
      username: '',
      password: '',
      email: '',
      full_name: '',
    });
  };

  if (checkingAuth) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Image source={require('../assets/logo.png')} style={styles.loadingLogo} />
          <Text style={styles.loadingText}>Loading {brand.name}...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" backgroundColor={colors.background} />
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer}>
          {/* Header */}
          <View style={styles.headerContainer}>
            <Image source={require('../assets/logo.png')} style={styles.logo} />
            <Text style={styles.appTitle}>{brand.name}</Text>
            <Text style={styles.subtitle}>{brand.tagline}</Text>
          </View>

          {/* Auth Form */}
          <Card style={styles.formCard}>
            <Text style={styles.formTitle}>
              {isLogin ? 'Welcome Back!' : 'Create Account'}
            </Text>
            
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                placeholder="Username"
                placeholderTextColor={colors.textSecondary}
                value={formData.username}
                onChangeText={(text) => setFormData({...formData, username: text})}
                autoCapitalize="none"
              />
            </View>

            {!isLogin && (
              <>
                <View style={styles.inputContainer}>
                  <TextInput
                    style={styles.input}
                    placeholder="Full Name"
                    placeholderTextColor={colors.textSecondary}
                    value={formData.full_name}
                    onChangeText={(text) => setFormData({...formData, full_name: text})}
                  />
                </View>

                <View style={styles.inputContainer}>
                  <TextInput
                    style={styles.input}
                    placeholder="Email"
                    placeholderTextColor={colors.textSecondary}
                    value={formData.email}
                    onChangeText={(text) => setFormData({...formData, email: text})}
                    keyboardType="email-address"
                    autoCapitalize="none"
                  />
                </View>
              </>
            )}

            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                placeholder="Password"
                placeholderTextColor={colors.textSecondary}
                value={formData.password}
                onChangeText={(text) => setFormData({...formData, password: text})}
                secureTextEntry
              />
            </View>

            <Button
              title={loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Sign Up')}
              onPress={handleAuth}
              disabled={loading}
              style={styles.authButton}
            />

            <TouchableOpacity onPress={toggleAuthMode} style={styles.toggleButton}>
              <Text style={styles.toggleText}>
                {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Sign In"}
              </Text>
            </TouchableOpacity>
          </Card>

          {/* Features Preview */}
          <Card style={styles.featuresCard}>
            <Text style={styles.featuresTitle}>What you'll get:</Text>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>🏔️</Text>
              <Text style={styles.featureText}>Best Travel Agents</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>🚗</Text>
              <Text style={styles.featureText}>Reliable Transport</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>💰</Text>
              <Text style={styles.featureText}>Sponsored Prices</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>🎯</Text>
              <Text style={styles.featureText}>Budget Travel Planner</Text>
            </View>
          </Card>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" backgroundColor="#2196F3" />
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer}>
          {/* Header */}
          <View style={styles.headerContainer}>
            <Text style={styles.appTitle}>TravelHub</Text>
            <Text style={styles.subtitle}>Your Travel & Transport Partner</Text>
          </View>

          {/* Auth Form */}
          <View style={styles.formContainer}>
            <Text style={styles.formTitle}>
              {isLogin ? 'Welcome Back!' : 'Create Account'}
            </Text>
            
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                placeholder="Username"
                placeholderTextColor="#9E9E9E"
                value={formData.username}
                onChangeText={(text) => setFormData({...formData, username: text})}
                autoCapitalize="none"
              />
            </View>

            {!isLogin && (
              <>
                <View style={styles.inputContainer}>
                  <TextInput
                    style={styles.input}
                    placeholder="Full Name"
                    placeholderTextColor="#9E9E9E"
                    value={formData.full_name}
                    onChangeText={(text) => setFormData({...formData, full_name: text})}
                  />
                </View>

                <View style={styles.inputContainer}>
                  <TextInput
                    style={styles.input}
                    placeholder="Email"
                    placeholderTextColor="#9E9E9E"
                    value={formData.email}
                    onChangeText={(text) => setFormData({...formData, email: text})}
                    keyboardType="email-address"
                    autoCapitalize="none"
                  />
                </View>
              </>
            )}

            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                placeholder="Password"
                placeholderTextColor="#9E9E9E"
                value={formData.password}
                onChangeText={(text) => setFormData({...formData, password: text})}
                secureTextEntry
              />
            </View>

            <TouchableOpacity 
              style={[styles.authButton, loading && styles.authButtonDisabled]}
              onPress={handleAuth}
              disabled={loading}
            >
              <Text style={styles.authButtonText}>
                {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Sign Up')}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={toggleAuthMode} style={styles.toggleButton}>
              <Text style={styles.toggleText}>
                {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Sign In"}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Features Preview */}
          <View style={styles.featuresContainer}>
            <Text style={styles.featuresTitle}>What you'll get:</Text>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>🏔️</Text>
              <Text style={styles.featureText}>Best Travel Agents</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>🚗</Text>
              <Text style={styles.featureText}>Reliable Transport</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>💰</Text>
              <Text style={styles.featureText}>Best Prices</Text>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    ...layout.safeArea,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  loadingLogo: {
    width: brand.logoSize.large,
    height: brand.logoSize.large,
    marginBottom: spacing.md,
    tintColor: colors.primary,
  },
  loadingText: {
    ...typography.h4,
    color: colors.primary,
  },
  scrollContainer: {
    flexGrow: 1,
    padding: spacing.md,
  },
  headerContainer: {
    alignItems: 'center',
    marginTop: spacing.xl,
    marginBottom: spacing.xl,
  },
  logo: {
    width: brand.logoSize.large,
    height: brand.logoSize.large,
    marginBottom: spacing.md,
    tintColor: colors.primary,
  },
  appTitle: {
    ...typography.h1,
    color: colors.primary,
    marginBottom: spacing.xs,
  },
  subtitle: {
    ...typography.body1,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  formCard: {
    marginBottom: spacing.lg,
  },
  formTitle: {
    ...typography.h3,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  inputContainer: {
    marginBottom: spacing.md,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.primaryLight,
    borderRadius: radius.md,
    paddingVertical: spacing.sm + 4,
    paddingHorizontal: spacing.md,
    ...typography.body1,
    backgroundColor: colors.surface,
    ...shadows.small,
  },
  authButton: {
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
  toggleButton: {
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  toggleText: {
    ...typography.body2,
    color: colors.primary,
  },
  featuresCard: {
    marginBottom: spacing.lg,
  },
  featuresTitle: {
    ...typography.h4,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  featureIcon: {
    fontSize: 24,
    marginRight: spacing.sm,
  },
  featureText: {
    ...typography.body1,
    color: colors.textSecondary,
  },
});