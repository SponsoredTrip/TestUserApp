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
  FlatList,
  Image,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Agent {
  id: string;
  name: string;
  type: string;
  description: string;
  rating: number;
  total_bookings: number;
  location: string;
  image_base64: string;
}

interface RibbonContent {
  id: string;
  title: string;
  type: string;
  items: any[];
  order: number;
}

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [ribbons, setRibbons] = useState<RibbonContent[]>([]);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      const userData = await AsyncStorage.getItem('user_data');
      
      if (!token) {
        router.replace('/');
        return;
      }

      if (userData) {
        setUser(JSON.parse(userData));
      }

      // Initialize sample data
      await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/init-data`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      // Load agents
      const agentsResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/agents`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (agentsResponse.ok) {
        const agentsData = await agentsResponse.json();
        setAgents(agentsData);
      }

      // Load ribbons
      const ribbonsResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/ribbons`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (ribbonsResponse.ok) {
        const ribbonsData = await ribbonsResponse.json();
        setRibbons(ribbonsData);
      }

    } catch (error) {
      console.error('Error loading data:', error);
      Alert.alert('Error', 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await AsyncStorage.removeItem('auth_token');
    await AsyncStorage.removeItem('user_data');
    router.replace('/');
  };

  const filterAgents = () => {
    let filtered = agents;
    
    if (selectedFilter !== 'all') {
      filtered = agents.filter(agent => agent.type === selectedFilter);
    }
    
    if (searchQuery) {
      filtered = filtered.filter(agent => 
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.location.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    return filtered;
  };

  const renderFilterRibbon = (ribbon: RibbonContent) => {
    if (ribbon.type !== 'filter') return null;
    
    return (
      <View key={ribbon.id} style={styles.ribbonContainer}>
        <Text style={styles.ribbonTitle}>{ribbon.title}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterScroll}>
          <TouchableOpacity
            style={[styles.filterChip, selectedFilter === 'all' && styles.filterChipActive]}
            onPress={() => setSelectedFilter('all')}
          >
            <Text style={[styles.filterChipText, selectedFilter === 'all' && styles.filterChipTextActive]}>
              All
            </Text>
          </TouchableOpacity>
          {ribbon.items.map((item, index) => (
            <TouchableOpacity
              key={index}
              style={[styles.filterChip, selectedFilter === item.value && styles.filterChipActive]}
              onPress={() => setSelectedFilter(item.value)}
            >
              <Text style={styles.filterIcon}>{item.icon}</Text>
              <Text style={[styles.filterChipText, selectedFilter === item.value && styles.filterChipTextActive]}>
                {item.name}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    );
  };

  const renderRecommendationRibbon = (ribbon: RibbonContent) => {
    if (ribbon.type !== 'recommendation') return null;
    
    const recommendedAgents = ribbon.items.map(item => 
      agents.find(agent => agent.id === item.agent_id)
    ).filter(Boolean);

    return (
      <View key={ribbon.id} style={styles.ribbonContainer}>
        <Text style={styles.ribbonTitle}>{ribbon.title}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {recommendedAgents.map((agent) => (
            <TouchableOpacity key={agent!.id} style={styles.recommendationCard}>
              <View style={styles.agentImagePlaceholder}>
                <Text style={styles.agentImageText}>{agent!.name[0]}</Text>
              </View>
              <Text style={styles.recommendationName} numberOfLines={1}>{agent!.name}</Text>
              <Text style={styles.recommendationRating}>⭐ {agent!.rating}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    );
  };

  const renderExploreRibbon = (ribbon: RibbonContent) => {
    if (ribbon.type !== 'explore') return null;
    
    return (
      <View key={ribbon.id} style={styles.ribbonContainer}>
        <Text style={styles.ribbonTitle}>{ribbon.title}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {ribbon.items.map((item, index) => (
            <TouchableOpacity key={index} style={styles.exploreCard}>
              <Text style={styles.exploreIcon}>{item.image}</Text>
              <Text style={styles.exploreName}>{item.category}</Text>
              <Text style={styles.exploreCount}>{item.count} options</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    );
  };

  const renderAgentCard = ({ item }: { item: Agent }) => (
    <TouchableOpacity 
      style={styles.agentCard}
      onPress={() => router.push(`/agent-details?id=${item.id}`)}
    >
      <View style={styles.agentImagePlaceholder}>
        <Text style={styles.agentImageText}>{item.name[0]}</Text>
      </View>
      <View style={styles.agentInfo}>
        <Text style={styles.agentName}>{item.name}</Text>
        <Text style={styles.agentDescription} numberOfLines={2}>{item.description}</Text>
        <Text style={styles.agentLocation}>📍 {item.location}</Text>
        <View style={styles.agentStats}>
          <Text style={styles.agentRating}>⭐ {item.rating}</Text>
          <Text style={styles.agentBookings}>{item.total_bookings} bookings</Text>
          <View style={[styles.agentTypeBadge, 
            item.type === 'travel' ? styles.travelBadge : styles.transportBadge
          ]}>
            <Text style={styles.agentTypeText}>
              {item.type === 'travel' ? '🏔️ Travel' : '🚗 Transport'}
            </Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
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

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" backgroundColor="#2196F3" />
      
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.welcomeText}>Welcome,</Text>
          <Text style={styles.userName}>{user?.username || 'User'}</Text>
        </View>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search agents, locations..."
          placeholderTextColor="#9E9E9E"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Dynamic Ribbons */}
        {ribbons.map(ribbon => {
          switch (ribbon.type) {
            case 'filter':
              return renderFilterRibbon(ribbon);
            case 'recommendation':
              return renderRecommendationRibbon(ribbon);
            case 'explore':
              return renderExploreRibbon(ribbon);
            default:
              return null;
          }
        })}

        {/* Agents List */}
        <View style={styles.agentsSection}>
          <Text style={styles.sectionTitle}>
            {selectedFilter === 'all' ? 'All Agents' : 
             selectedFilter === 'travel' ? 'Travel Agents' : 'Transport Agents'}
          </Text>
          <FlatList
            data={filterAgents()}
            renderItem={renderAgentCard}
            keyExtractor={(item) => item.id}
            scrollEnabled={false}
            showsVerticalScrollIndicator={false}
          />
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
  header: {
    backgroundColor: '#2196F3',
    padding: 20,
    paddingTop: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  welcomeText: {
    color: 'white',
    fontSize: 16,
  },
  userName: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  logoutButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  logoutText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '500',
  },
  searchContainer: {
    padding: 16,
    backgroundColor: 'white',
  },
  searchInput: {
    backgroundColor: '#F5F5F5',
    borderRadius: 25,
    padding: 16,
    fontSize: 16,
    color: '#333',
  },
  content: {
    flex: 1,
  },
  ribbonContainer: {
    backgroundColor: 'white',
    marginBottom: 8,
    paddingVertical: 16,
  },
  ribbonTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  filterScroll: {
    paddingLeft: 16,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 12,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  filterChipActive: {
    backgroundColor: '#2196F3',
    borderColor: '#2196F3',
  },
  filterIcon: {
    fontSize: 16,
    marginRight: 4,
  },
  filterChipText: {
    color: '#666',
    fontSize: 14,
    fontWeight: '500',
  },
  filterChipTextActive: {
    color: 'white',
  },
  recommendationCard: {
    width: 120,
    alignItems: 'center',
    marginRight: 16,
    marginLeft: 16,
  },
  recommendationName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginTop: 8,
    textAlign: 'center',
  },
  recommendationRating: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  exploreCard: {
    width: 140,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginRight: 16,
    marginLeft: 16,
  },
  exploreIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  exploreName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
    marginBottom: 4,
  },
  exploreCount: {
    fontSize: 12,
    color: '#666',
  },
  agentsSection: {
    backgroundColor: 'white',
    paddingTop: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  agentCard: {
    flexDirection: 'row',
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 12,
    backgroundColor: 'white',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  agentImagePlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 12,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  agentImageText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  agentInfo: {
    flex: 1,
  },
  agentName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  agentDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  agentLocation: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  agentStats: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  agentRating: {
    fontSize: 12,
    color: '#333',
    marginRight: 16,
  },
  agentBookings: {
    fontSize: 12,
    color: '#666',
    marginRight: 16,
  },
  agentTypeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  travelBadge: {
    backgroundColor: '#E8F5E8',
  },
  transportBadge: {
    backgroundColor: '#FFF3E0',
  },
  agentTypeText: {
    fontSize: 10,
    fontWeight: '500',
    color: '#333',
  },
});