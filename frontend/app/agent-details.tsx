import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  FlatList,
  Image,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router, useLocalSearchParams } from 'expo-router';
import { colors, layout, spacing, typography, shadows, radius, brand } from '../constants/theme';
import { Card } from '../components/UI/Card';
import { Button } from '../components/UI/Button';
import { ChatModal } from '../components/UI/ChatModal';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Agent {
  id: string;
  name: string;
  type: string;
  description: string;
  rating: number;
  total_bookings: number;
  location: string;
  contact_phone: string;
  contact_email: string;
  is_subscribed?: boolean;
  subscription_type?: string;
}

interface Package {
  id: string;
  agent_id: string;
  title: string;
  description: string;
  price: number;
  duration: string;
  destination: string;
  features: string[];
  is_sponsored?: boolean;
  original_price?: number;
  sponsored_price?: number;
  discount_percentage?: number;
}

export default function AgentDetails() {
  const { id } = useLocalSearchParams();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [packages, setPackages] = useState<Package[]>([]);
  const [loading, setLoading] = useState(true);
  const [showChatModal, setShowChatModal] = useState(false);
  const [selectedPackage, setSelectedPackage] = useState<Package | null>(null);

  useEffect(() => {
    if (id) {
      loadAgentDetails();
    }
  }, [id]);

  const loadAgentDetails = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        router.replace('/');
        return;
      }

      // Load agent details
      const agentResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/agents/${id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (agentResponse.ok) {
        const agentData = await agentResponse.json();
        setAgent(agentData);
      }

      // Load packages for this agent
      const packagesResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/packages?agent_id=${id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (packagesResponse.ok) {
        const packagesData = await packagesResponse.json();
        setPackages(packagesData);
      }

    } catch (error) {
      console.error('Error loading agent details:', error);
      Alert.alert('Error', 'Failed to load agent details');
    } finally {
      setLoading(false);
    }
  };

  const handleBookPackage = async (packageId: string) => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        router.replace('/');
        return;
      }

      const travelDate = new Date();
      travelDate.setDate(travelDate.getDate() + 7); // Default to 7 days from now

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/bookings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          package_id: packageId,
          travel_date: travelDate.toISOString(),
        }),
      });

      if (response.ok) {
        Alert.alert('Success', 'Package booked successfully!');
      } else {
        const errorData = await response.json();
        Alert.alert('Error', errorData.detail || 'Booking failed');
      }
    } catch (error) {
      console.error('Booking error:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    }
  };

  const handleOpenChat = (packageItem: Package) => {
    setSelectedPackage(packageItem);
    setShowChatModal(true);
  };

  const renderPackageCard = ({ item }: { item: Package }) => (
    <View style={styles.packageCard}>
      <View style={styles.packageHeader}>
        <Text style={styles.packageTitle}>{item.title}</Text>
        <View style={styles.priceContainer}>
          {item.is_sponsored && item.original_price && item.sponsored_price ? (
            <>
              <Text style={styles.originalPrice}>₹{item.original_price.toLocaleString()}</Text>
              <Text style={styles.sponsoredPrice}>₹{item.sponsored_price.toLocaleString()}</Text>
              {item.discount_percentage && (
                <Text style={styles.discountBadge}>{item.discount_percentage}% OFF</Text>
              )}
            </>
          ) : (
            <Text style={styles.packagePrice}>₹{item.price.toLocaleString()}</Text>
          )}
        </View>
      </View>
      
      <Text style={styles.packageDescription}>{item.description}</Text>
      
      <View style={styles.packageDetails}>
        <Text style={styles.packageDetail}>📍 {item.destination}</Text>
        <Text style={styles.packageDetail}>⏱️ {item.duration}</Text>
      </View>

      {item.features && item.features.length > 0 && (
        <View style={styles.featuresContainer}>
          <Text style={styles.featuresTitle}>Includes:</Text>
          {item.features.map((feature, index) => (
            <Text key={index} style={styles.featureItem}>• {feature}</Text>
          ))}
        </View>
      )}

      <View style={styles.actionButtons}>
        <TouchableOpacity
          style={styles.bookButton}
          onPress={() => handleBookPackage(item.id)}
        >
          <Text style={styles.bookButtonText}>Book Now</Text>
        </TouchableOpacity>
        
        {agent?.is_subscribed && (
          <TouchableOpacity
            style={styles.messageButton}
            onPress={() => handleOpenChat(item)}
          >
            <Text style={styles.messageButtonText}>💬 Message</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!agent) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Agent not found</Text>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" backgroundColor="#2196F3" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Agent Details</Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Agent Info */}
        <View style={styles.agentCard}>
          <View style={styles.agentImagePlaceholder}>
            <Text style={styles.agentImageText}>{agent.name[0]}</Text>
          </View>
          
          <View style={styles.agentInfo}>
            <Text style={styles.agentName}>{agent.name}</Text>
            <Text style={styles.agentDescription}>{agent.description}</Text>
            
            <View style={styles.agentStats}>
              <Text style={styles.agentRating}>⭐ {agent.rating}</Text>
              <Text style={styles.agentBookings}>{agent.total_bookings} bookings</Text>
              <View style={[styles.agentTypeBadge, 
                agent.type === 'travel' ? styles.travelBadge : styles.transportBadge
              ]}>
                <Text style={styles.agentTypeText}>
                  {agent.type === 'travel' ? '🏔️ Travel' : '🚗 Transport'}
                </Text>
              </View>
            </View>

            <Text style={styles.agentLocation}>📍 {agent.location}</Text>
            
            <View style={styles.contactInfo}>
              <Text style={styles.contactItem}>📞 {agent.contact_phone}</Text>
              <Text style={styles.contactItem}>✉️ {agent.contact_email}</Text>
            </View>
          </View>
        </View>

        {/* Packages Section */}
        <View style={styles.packagesSection}>
          <Text style={styles.sectionTitle}>
            {agent.type === 'travel' ? 'Travel Packages' : 'Transport Services'}
          </Text>
          
          {packages.length > 0 ? (
            <FlatList
              data={packages}
              renderItem={renderPackageCard}
              keyExtractor={(item) => item.id}
              scrollEnabled={false}
              showsVerticalScrollIndicator={false}
            />
          ) : (
            <View style={styles.noPackagesContainer}>
              <Text style={styles.noPackagesText}>No packages available at the moment</Text>
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 18,
    color: '#2196F3',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 18,
    color: '#666',
    marginBottom: 20,
  },
  header: {
    backgroundColor: '#2196F3',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    padding: 8,
  },
  backButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '500',
  },
  headerTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  headerSpacer: {
    width: 60, // Balance the header
  },
  content: {
    flex: 1,
  },
  agentCard: {
    backgroundColor: 'white',
    margin: 16,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  agentImagePlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'center',
    marginBottom: 16,
  },
  agentImageText: {
    fontSize: 40,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  agentInfo: {
    alignItems: 'center',
  },
  agentName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
  },
  agentDescription: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 16,
    lineHeight: 22,
  },
  agentStats: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  agentRating: {
    fontSize: 14,
    color: '#333',
    marginHorizontal: 8,
    marginVertical: 4,
  },
  agentBookings: {
    fontSize: 14,
    color: '#666',
    marginHorizontal: 8,
    marginVertical: 4,
  },
  agentTypeBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginHorizontal: 8,
    marginVertical: 4,
  },
  travelBadge: {
    backgroundColor: '#E8F5E8',
  },
  transportBadge: {
    backgroundColor: '#FFF3E0',
  },
  agentTypeText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#333',
  },
  agentLocation: {
    fontSize: 16,
    color: '#666',
    marginBottom: 16,
    textAlign: 'center',
  },
  contactInfo: {
    alignItems: 'center',
  },
  contactItem: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  packagesSection: {
    margin: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  packageCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  packageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  packageTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
    marginRight: 12,
  },
  packagePrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  packageDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
    lineHeight: 20,
  },
  packageDetails: {
    marginBottom: 12,
  },
  packageDetail: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  featuresContainer: {
    marginBottom: 16,
  },
  featuresTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  featureItem: {
    fontSize: 13,
    color: '#666',
    marginBottom: 4,
    marginLeft: 8,
  },
  bookButton: {
    backgroundColor: '#2196F3',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  bookButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  noPackagesContainer: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
  },
  noPackagesText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
});