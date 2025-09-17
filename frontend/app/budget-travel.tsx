import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  ActivityIndicator,
  Image,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { colors, layout, spacing, typography, shadows, radius, brand } from '../constants/theme';
import { Card } from '../components/UI/Card';
import { Button } from '../components/UI/Button';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface PackageData {
  id: string;
  title: string;
  destination: string;
  duration_days: number;
  cost: number;
  agent_id: string;
}

interface TransportSegment {
  from: string;
  to: string;
  cost: number;
  distance_km: number;
  type: string;
}

interface PackageCombination {
  packages: PackageData[];
  transport_segments: TransportSegment[];
  total_cost: number;
  total_days: number;
  savings: number;
  itinerary_summary: string;
}

interface BudgetTravelRequest {
  budget: number;
  num_persons: number;
  num_days: number;
  place?: string;
}

interface BudgetTravelResponse {
  request: BudgetTravelRequest;
  combinations: PackageCombination[];
  total_combinations_found: number;
  message: string;
}

export default function BudgetTravel() {
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [formData, setFormData] = useState({
    budget: '',
    num_persons: '2',
    num_days: '6',
    place: '',
  });
  const [results, setResults] = useState<PackageCombination[]>([]);
  const [preview, setPreview] = useState<any>(null);

  useEffect(() => {
    loadPreview();
  }, []);

  const loadPreview = async () => {
    setLoading(true);
    try {
      const token = await AsyncStorage.getItem('auth_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/budget-travel/preview`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPreview(data);
      }
    } catch (error) {
      console.error('Preview error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDestinationGroupPress = (destination: string) => {
    // Set the place filter and trigger search
    setFormData({...formData, place: destination});
    handleSearch();
  };

  const handleSearch = async () => {
    if (!formData.budget || !formData.num_persons || !formData.num_days) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    const budget = parseFloat(formData.budget);
    const numPersons = parseInt(formData.num_persons);
    const numDays = parseInt(formData.num_days);

    if (budget <= 0 || numPersons <= 0 || numDays <= 0) {
      Alert.alert('Error', 'Please enter valid values');
      return;
    }

    setSearching(true);
    try {
      const token = await AsyncStorage.getItem('auth_token');
      const requestData: BudgetTravelRequest = {
        budget,
        num_persons: numPersons,
        num_days: numDays,
        place: formData.place || undefined,
      };

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/budget-travel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        const data: BudgetTravelResponse = await response.json();
        setResults(data.combinations);
        if (data.combinations.length === 0) {
          Alert.alert('No Results', data.message);
        }
      } else {
        const errorData = await response.json();
        Alert.alert('Error', errorData.detail || 'Search failed');
      }
    } catch (error) {
      console.error('Search error:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  const renderCombination = (combination: PackageCombination, index: number) => (
    <Card key={index} style={styles.combinationCard}>
      <Text style={styles.combinationTitle}>Option {index + 1}</Text>
      
      {/* Summary */}
      <View style={styles.summaryContainer}>
        <Text style={styles.summaryText}>{combination.itinerary_summary}</Text>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Total Days:</Text>
          <Text style={styles.summaryValue}>{combination.total_days}</Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Total Cost:</Text>
          <Text style={styles.summaryValue}>{brand.sponsoredPricePrefix}{combination.total_cost}</Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Savings:</Text>
          <Text style={[styles.summaryValue, styles.savingsText]}>₹{combination.savings}</Text>
        </View>
      </View>

      {/* Packages */}
      <Text style={styles.sectionTitle}>Packages Included:</Text>
      {combination.packages.map((pkg, pkgIndex) => (
        <View key={pkgIndex} style={styles.packageItem}>
          <Text style={styles.packageTitle}>{pkg.title}</Text>
          <Text style={styles.packageDestination}>{pkg.destination}</Text>
          <View style={styles.packageDetails}>
            <Text style={styles.packageDetail}>{pkg.duration_days} days</Text>
            <Text style={styles.packageDetail}>₹{pkg.cost}</Text>
          </View>
        </View>
      ))}

      {/* Transport */}
      {combination.transport_segments.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>Transport:</Text>
          {combination.transport_segments.map((transport, transportIndex) => (
            <View key={transportIndex} style={styles.transportItem}>
              <Text style={styles.transportRoute}>{transport.from} → {transport.to}</Text>
              <Text style={styles.transportDetails}>
                {transport.type} • {transport.distance_km}km • ₹{transport.cost}
              </Text>
            </View>
          ))}
        </>
      )}

      <Button
        title="Book This Combination"
        onPress={() => Alert.alert('Booking', 'Booking functionality coming soon!')}
        style={styles.bookButton}
      />
    </Card>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" backgroundColor={colors.background} />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Text style={styles.backButtonText}>←</Text>
        </TouchableOpacity>
        <Image source={require('../assets/logo.png')} style={styles.headerLogo} />
        <Text style={styles.headerTitle}>Budget Travel</Text>
      </View>

      <ScrollView style={styles.scrollContainer}>
        {/* Search Form */}
        <Card style={styles.searchCard}>
          <Text style={styles.searchTitle}>Plan Your Budget Trip</Text>
          
          <View style={styles.inputRow}>
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Budget (₹)</Text>
              <TextInput
                style={styles.input}
                placeholder="50000"
                placeholderTextColor={colors.textSecondary}
                value={formData.budget}
                onChangeText={(text) => setFormData({...formData, budget: text})}
                keyboardType="numeric"
              />
            </View>
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Persons</Text>
              <TextInput
                style={styles.input}
                placeholder="2"
                placeholderTextColor={colors.textSecondary}
                value={formData.num_persons}
                onChangeText={(text) => setFormData({...formData, num_persons: text})}
                keyboardType="numeric"
              />
            </View>
          </View>

          <View style={styles.inputRow}>
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Days</Text>
              <TextInput
                style={styles.input}
                placeholder="6"
                placeholderTextColor={colors.textSecondary}
                value={formData.num_days}
                onChangeText={(text) => setFormData({...formData, num_days: text})}
                keyboardType="numeric"
              />
            </View>
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Place (Optional)</Text>
              <TextInput
                style={styles.input}
                placeholder="Goa"
                placeholderTextColor={colors.textSecondary}
                value={formData.place}
                onChangeText={(text) => setFormData({...formData, place: text})}
                autoCapitalize="words"
              />
            </View>
          </View>

          <Button
            title={searching ? 'Searching...' : 'Find Best Combinations'}
            onPress={handleSearch}
            disabled={searching}
            style={styles.searchButton}
          />
        </Card>

        {/* Preview Info with Destination Groups */}
        {preview && !searching && results.length === 0 && (
          <Card style={styles.previewCard}>
            <Text style={styles.previewTitle}>Available Destination Groups</Text>
            
            {/* Goa Group */}
            <TouchableOpacity style={styles.destinationGroup} onPress={() => handleDestinationGroupPress('Goa')}>
              <View style={styles.groupHeader}>
                <Text style={styles.groupIcon}>🏖️</Text>
                <View style={styles.groupInfo}>
                  <Text style={styles.groupName}>Goa Beach Paradise</Text>
                  <Text style={styles.groupDescription}>3-5 days • ₹8,000-₹15,000 per person</Text>
                  <Text style={styles.groupPackages}>Multiple packages available</Text>
                </View>
              </View>
            </TouchableOpacity>

            {/* Himachal Group */}
            <TouchableOpacity style={styles.destinationGroup} onPress={() => handleDestinationGroupPress('Himachal')}>
              <View style={styles.groupHeader}>
                <Text style={styles.groupIcon}>⛰️</Text>
                <View style={styles.groupInfo}>
                  <Text style={styles.groupName}>Himachal Adventures</Text>
                  <Text style={styles.groupDescription}>5-12 days • ₹15,000-₹35,000 per person</Text>
                  <Text style={styles.groupPackages}>Trekking & Hill Station packages</Text>
                </View>
              </View>
            </TouchableOpacity>
            
            {/* Uttarakhand Group */}
            <TouchableOpacity style={styles.destinationGroup} onPress={() => handleDestinationGroupPress('Uttarakhand')}>
              <View style={styles.groupHeader}>
                <Text style={styles.groupIcon}>🏔️</Text>
                <View style={styles.groupInfo}>
                  <Text style={styles.groupName}>Uttarakhand Escapes</Text>
                  <Text style={styles.groupDescription}>4-8 days • ₹12,000-₹25,000 per person</Text>
                  <Text style={styles.groupPackages}>Spiritual & Adventure tours</Text>
                </View>
              </View>
            </TouchableOpacity>
            
            <Text style={styles.previewText}>
              Total {preview.total_packages} packages available across all destinations
            </Text>
          </Card>
        )}

        {/* Loading */}
        {searching && (
          <Card style={styles.loadingCard}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={styles.loadingText}>Finding the best combinations...</Text>
          </Card>
        )}

        {/* Results */}
        {results.length > 0 && (
          <View style={styles.resultsContainer}>
            <Text style={styles.resultsTitle}>Found {results.length} Combinations</Text>
            {results.map((combination, index) => renderCombination(combination, index))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    ...layout.safeArea,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.primaryLight,
    ...shadows.small,
  },
  backButton: {
    padding: spacing.xs,
    marginRight: spacing.sm,
  },
  backButtonText: {
    fontSize: 24,
    color: colors.primary,
  },
  headerLogo: {
    width: brand.logoSize.small,
    height: brand.logoSize.small,
    marginRight: spacing.xs,
    tintColor: colors.primary,
  },
  headerTitle: {
    ...typography.h3,
    color: colors.primary,
  },
  scrollContainer: {
    flex: 1,
    padding: spacing.md,
  },
  searchCard: {
    marginBottom: spacing.md,
  },
  searchTitle: {
    ...typography.h4,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  inputRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  inputContainer: {
    flex: 1,
    marginHorizontal: spacing.xs,
  },
  inputLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
    textTransform: 'uppercase',
  },
  input: {
    borderWidth: 1,
    borderColor: colors.primaryLight,
    borderRadius: radius.md,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm,
    ...typography.body1,
    backgroundColor: colors.surface,
    ...shadows.small,
  },
  searchButton: {
    marginTop: spacing.md,
  },
  previewCard: {
    marginBottom: spacing.md,
  },
  previewTitle: {
    ...typography.h4,
    marginBottom: spacing.sm,
  },
  previewText: {
    ...typography.body2,
    marginBottom: spacing.xs,
  },
  loadingCard: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
  loadingText: {
    ...typography.body1,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
  resultsContainer: {
    marginTop: spacing.md,
  },
  resultsTitle: {
    ...typography.h3,
    marginBottom: spacing.md,
    textAlign: 'center',
    color: colors.primary,
  },
  combinationCard: {
    marginBottom: spacing.md,
    padding: spacing.md + 4,
  },
  combinationTitle: {
    ...typography.h4,
    color: colors.primary,
    marginBottom: spacing.sm,
  },
  summaryContainer: {
    backgroundColor: colors.primaryLight,
    borderRadius: radius.md,
    padding: spacing.sm,
    marginBottom: spacing.md,
  },
  summaryText: {
    ...typography.body1,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  summaryLabel: {
    ...typography.body2,
  },
  summaryValue: {
    ...typography.body1,
    fontWeight: '600',
  },
  savingsText: {
    color: colors.success,
  },
  sectionTitle: {
    ...typography.h4,
    marginBottom: spacing.sm,
    marginTop: spacing.sm,
  },
  packageItem: {
    backgroundColor: colors.surfaceLight,
    borderRadius: radius.md,
    padding: spacing.sm,
    marginBottom: spacing.sm,
  },
  packageTitle: {
    ...typography.body1,
    fontWeight: '600',
    marginBottom: spacing.xs,
  },
  packageDestination: {
    ...typography.body2,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  packageDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  packageDetail: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '600',
  },
  transportItem: {
    backgroundColor: colors.surfaceLight,
    borderRadius: radius.md,
    padding: spacing.sm,
    marginBottom: spacing.sm,
  },
  transportRoute: {
    ...typography.body1,
    fontWeight: '600',
    marginBottom: spacing.xs,
  },
  transportDetails: {
    ...typography.body2,
    color: colors.textSecondary,
  },
  bookButton: {
    marginTop: spacing.md,
  },
});