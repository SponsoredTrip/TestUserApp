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
  ActivityIndicator,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { colors, layout, spacing, typography, shadows, radius, brand } from '../constants/theme';
import { Card } from '../components/UI/Card';
import { Button } from '../components/UI/Button';
import { Avatar } from '../components/UI/Avatar';
import { AdvancedFilterModal, FilterOptions } from '../components/UI/AdvancedFilterModal';

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
  is_subscribed?: boolean;
  subscription_type?: string;
  avatar_id?: string;
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
  const [filteredAgents, setFilteredAgents] = useState<Agent[]>([]);
  const [ribbons, setRibbons] = useState<RibbonContent[]>([]);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const [showAdvancedFilter, setShowAdvancedFilter] = useState(false);
  const [advancedFilters, setAdvancedFilters] = useState<FilterOptions>({
    sortBy: 'relevance',
    dateFrom: null,
    dateTo: null,
    rating: 'all',
    sponsored: 'all',
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (agents.length > 0) {
      applyFilters();
    }
  }, [selectedFilter, searchQuery, agents]);

  const applyFilters = async () => {
    let filtered = agents;
    
    if (selectedFilter !== 'all') {
      // Handle sponsored filter - fetch agents with sponsored packages from backend
      if (selectedFilter === 'sponsored') {
        try {
          const token = await AsyncStorage.getItem('auth_token');
          const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/agents?agent_type=sponsored`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
          
          if (response.ok) {
            const sponsoredAgents = await response.json();
            filtered = sponsoredAgents;
          } else {
            // Fallback to subscribed agents if API fails
            filtered = agents.filter(agent => agent.is_subscribed === true);
          }
        } catch (error) {
          console.error('Error fetching sponsored agents:', error);
          // Fallback to subscribed agents if API fails
          filtered = agents.filter(agent => agent.is_subscribed === true);
        }
      }
      // Handle agent type filters
      else if (selectedFilter === 'travel' || selectedFilter === 'transport') {
        filtered = agents.filter(agent => agent.type === selectedFilter);
      }
      // Handle location-based filters
      else if (['goa', 'himachal', 'uttarakhand'].includes(selectedFilter)) {
        filtered = agents.filter(agent => 
          agent.location.toLowerCase().includes(selectedFilter) ||
          agent.location.toLowerCase().includes(selectedFilter === 'himachal' ? 'shimla' : selectedFilter === 'uttarakhand' ? 'dehradun' : 'goa')
        );
      }
    }
    
    if (searchQuery) {
      filtered = filtered.filter(agent => 
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.location.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    setFilteredAgents(filtered);
  };

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
        setFilteredAgents(agentsData); // Initialize filtered agents
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

  const filterAgents = async () => {
    let filtered = agents;
    
    if (selectedFilter !== 'all') {
      // Handle sponsored filter - fetch agents with sponsored packages from backend
      if (selectedFilter === 'sponsored') {
        try {
          const token = await AsyncStorage.getItem('auth_token');
          const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/agents?agent_type=sponsored`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
          
          if (response.ok) {
            const sponsoredAgents = await response.json();
            filtered = sponsoredAgents;
          } else {
            // Fallback to subscribed agents if API fails
            filtered = agents.filter(agent => agent.is_subscribed === true);
          }
        } catch (error) {
          console.error('Error fetching sponsored agents:', error);
          // Fallback to subscribed agents if API fails
          filtered = agents.filter(agent => agent.is_subscribed === true);
        }
      }
      // Handle agent type filters
      else if (selectedFilter === 'travel' || selectedFilter === 'transport') {
        filtered = agents.filter(agent => agent.type === selectedFilter);
      }
      // Handle location-based filters
      else if (['goa', 'himachal', 'uttarakhand'].includes(selectedFilter)) {
        filtered = agents.filter(agent => 
          agent.location.toLowerCase().includes(selectedFilter) ||
          agent.location.toLowerCase().includes(selectedFilter === 'himachal' ? 'shimla' : selectedFilter === 'uttarakhand' ? 'dehradun' : 'goa')
        );
      }
    }
    
    if (searchQuery) {
      filtered = filtered.filter(agent => 
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.location.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    return filtered;
  };

  const handleExploreItemPress = (item: any) => {
    if (item.action === 'budget_travel') {
      router.push('/budget-travel');
    } else {
      Alert.alert('Coming Soon', `${item.category} feature will be available soon!`);
    }
  };

  const renderFilterRibbon = (ribbon: RibbonContent) => {
    if (ribbon.type !== 'filter') return null;
    
    return (
      <Card key={ribbon.id} style={styles.ribbonCard}>
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
      </Card>
    );
  };

  const renderRecommendationRibbon = (ribbon: RibbonContent) => {
    if (ribbon.type !== 'recommendation') return null;
    
    const recommendedAgents = ribbon.items.map(item => 
      agents.find(agent => agent.id === item.agent_id)
    ).filter(Boolean);

    return (
      <Card key={ribbon.id} style={styles.ribbonCard}>
        <Text style={styles.ribbonTitle}>{ribbon.title}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {recommendedAgents.map((agent) => (
            <TouchableOpacity 
              key={agent!.id} 
              style={styles.recommendationCard}
              onPress={() => router.push(`/agent-details?id=${agent!.id}`)}
            >
              <Avatar 
                avatar_id={agent!.avatar_id}
                name={agent!.name}
                size="medium"
              />
              <Text style={styles.recommendationName} numberOfLines={1}>{agent!.name}</Text>
              <Text style={styles.recommendationRating}>⭐ {agent!.rating}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </Card>
    );
  };

  const renderExploreRibbon = (ribbon: RibbonContent) => {
    if (ribbon.type !== 'explore') return null;
    
    return (
      <Card key={ribbon.id} style={styles.ribbonCard}>
        <Text style={styles.ribbonTitle}>{ribbon.title}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {ribbon.items.map((item, index) => (
            <TouchableOpacity 
              key={index} 
              style={[
                styles.exploreCard,
                item.action === 'budget_travel' && styles.budgetTravelCard
              ]}
              onPress={() => handleExploreItemPress(item)}
            >
              <Text style={[
                styles.exploreIcon,
                item.action === 'budget_travel' && styles.budgetTravelIcon
              ]}>
                {item.image}
              </Text>
              <Text style={[
                styles.exploreName,
                item.action === 'budget_travel' && styles.budgetTravelName
              ]}>
                {item.category}
              </Text>
              <Text style={styles.exploreCount}>{item.count} options</Text>
              {item.action === 'budget_travel' && (
                <View style={styles.budgetBadge}>
                  <Text style={styles.budgetBadgeText}>NEW</Text>
                </View>
              )}
            </TouchableOpacity>
          ))}
        </ScrollView>
      </Card>
    );
  };

  const renderAgentCard = ({ item }: { item: Agent }) => (
    <Card style={styles.agentCard}>
      <TouchableOpacity 
        style={styles.agentCardContent}
        onPress={() => router.push(`/agent-details?id=${item.id}`)}
      >
        <Avatar 
          avatar_id={item.avatar_id}
          name={item.name}
          size="medium"
          style={styles.agentAvatar}
        />
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
    </Card>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Image source={require('../assets/logo.png')} style={styles.loadingLogo} />
          <ActivityIndicator size="large" color={colors.primary} style={styles.loadingSpinner} />
          <Text style={styles.loadingText}>Loading {brand.name}...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" backgroundColor={colors.background} />
      
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Image source={require('../assets/logo.png')} style={styles.headerLogo} />
          <View>
            <Text style={styles.welcomeText}>Welcome,</Text>
            <Text style={styles.userName}>{user?.username || 'User'}</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>

      {/* Search Bar */}
      <Card style={styles.searchCard}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search agents, locations..."
          placeholderTextColor={colors.textSecondary}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </Card>

      {/* Sticky Filter Ribbon - Outside ScrollView */}
      <View style={styles.stickyFilterContainer}>
        {ribbons.filter(ribbon => ribbon.type === 'filter').map(ribbon => (
          <View key={ribbon.id} style={styles.stickyFilterContent}>
            <Text style={styles.stickyFilterTitle}>{ribbon.title}</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterScroll}>
              {/* Advanced Filter Dropdown Button */}
              <TouchableOpacity
                style={[styles.filterChip, styles.advancedFilterChip]}
                onPress={() => setShowAdvancedFilter(true)}
              >
                <Text style={styles.filterChipText}>All</Text>
                <Text style={styles.dropdownIcon}>▼</Text>
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
        ))}
      </View>

      {/* Scrollable Content */}
      <ScrollView style={styles.scrollableContent} showsVerticalScrollIndicator={false}>
        {/* Other Dynamic Ribbons */}
        {ribbons.filter(ribbon => ribbon.type !== 'filter').map(ribbon => {
          switch (ribbon.type) {
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
             selectedFilter === 'travel' ? 'Travel Agents' : 
             selectedFilter === 'transport' ? 'Transport Agents' :
             selectedFilter === 'sponsored' ? 'Sponsored Agents' :
             `${selectedFilter.charAt(0).toUpperCase() + selectedFilter.slice(1)} Agents`}
          </Text>
          <FlatList
            data={filteredAgents}
            renderItem={renderAgentCard}
            keyExtractor={(item) => item.id}
            scrollEnabled={false}
            showsVerticalScrollIndicator={false}
          />
        </View>
      </ScrollView>

      {/* Advanced Filter Modal */}
      <AdvancedFilterModal
        visible={showAdvancedFilter}
        onClose={() => setShowAdvancedFilter(false)}
        onApplyFilters={(filters) => {
          setAdvancedFilters(filters);
          // Apply filters logic here
          console.log('Applied filters:', filters);
        }}
        currentFilters={advancedFilters}
      />
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
  loadingSpinner: {
    marginVertical: spacing.md,
  },
  loadingText: {
    ...typography.h4,
    color: colors.primary,
  },
  header: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 4,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: colors.primaryLight,
    ...shadows.small,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerLogo: {
    width: brand.logoSize.medium,
    height: brand.logoSize.medium,
    marginRight: spacing.sm,
    tintColor: colors.primary,
  },
  welcomeText: {
    ...typography.body2,
    color: colors.textSecondary,
  },
  userName: {
    ...typography.h4,
    color: colors.primary,
  },
  logoutButton: {
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    borderRadius: radius.xl,
    ...shadows.small,
  },
  logoutText: {
    ...typography.body2,
    color: colors.primary,
    fontWeight: '600',
  },
  searchCard: {
    margin: spacing.md,
    marginBottom: spacing.sm,
  },
  searchInput: {
    ...typography.body1,
    color: colors.text,
    paddingVertical: spacing.sm,
    paddingHorizontal: 0,
  },
  stickyFilterContainer: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.primaryLight + '30',
    ...shadows.small,
    position: 'relative',
    zIndex: 100,
  },
  stickyFilterContent: {
    backgroundColor: colors.surface,
  },
  stickyFilterTitle: {
    ...typography.h4,
    marginBottom: spacing.sm,
  },
  scrollableContent: {
    flex: 1,
    paddingHorizontal: spacing.md,
  },
  ribbonCard: {
    marginBottom: spacing.sm,
  },
  ribbonTitle: {
    ...typography.h4,
    marginBottom: spacing.md,
  },
  filterScroll: {
    paddingRight: spacing.md,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    marginRight: spacing.sm,
    borderRadius: radius.xl,
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderColor: colors.primaryLight,
    ...shadows.small,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterIcon: {
    fontSize: 16,
    marginRight: spacing.xs,
  },
  filterChipText: {
    ...typography.body2,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  filterChipTextActive: {
    color: colors.textLight,
  },
  advancedFilterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md + 4,
  },
  dropdownIcon: {
    fontSize: 12,
    color: colors.textSecondary,
    marginLeft: spacing.xs,
  },
  recommendationCard: {
    width: 120,
    alignItems: 'center',
    marginRight: spacing.md,
    marginLeft: spacing.xs,
  },
  recommendationName: {
    ...typography.body2,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: spacing.xs,
  },
  recommendationRating: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs / 2,
  },
  exploreCard: {
    width: 140,
    backgroundColor: colors.surfaceLight,
    borderRadius: radius.lg,
    padding: spacing.md,
    alignItems: 'center',
    marginRight: spacing.md,
    marginLeft: spacing.xs,
    ...shadows.small,
    position: 'relative',
  },
  budgetTravelCard: {
    backgroundColor: colors.primary + '10',
    borderWidth: 2,
    borderColor: colors.primary + '40',
    ...shadows.medium,
  },
  exploreIcon: {
    fontSize: 32,
    marginBottom: spacing.xs,
  },
  budgetTravelIcon: {
    fontSize: 40,
    marginBottom: spacing.xs + 2,
  },
  exploreName: {
    ...typography.body2,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: spacing.xs / 2,
  },
  budgetTravelName: {
    ...typography.body2,
    fontWeight: 'bold',
    color: colors.primary,
    textAlign: 'center',
    marginBottom: spacing.xs / 2,
  },
  exploreCount: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  budgetBadge: {
    position: 'absolute',
    top: spacing.xs,
    right: spacing.xs,
    backgroundColor: colors.success,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.xs,
    paddingVertical: 2,
  },
  budgetBadgeText: {
    color: colors.textLight,
    fontSize: 10,
    fontWeight: 'bold',
  },
  agentsSection: {
    marginTop: spacing.sm,
  },
  sectionTitle: {
    ...typography.h4,
    marginBottom: spacing.md,
  },
  agentCard: {
    marginBottom: spacing.sm,
    padding: 0,
  },
  agentCardContent: {
    flexDirection: 'row',
    padding: spacing.md,
  },
  agentAvatar: {
    marginRight: spacing.md,
  },
  agentImagePlaceholder: {
    width: 80,
    height: 80,
    borderRadius: radius.lg,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  agentImageText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: colors.primary,
  },
  agentInfo: {
    flex: 1,
  },
  agentName: {
    ...typography.body1,
    fontWeight: 'bold',
    marginBottom: spacing.xs / 2,
  },
  agentDescription: {
    ...typography.body2,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  agentLocation: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  agentStats: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  agentRating: {
    ...typography.caption,
    marginRight: spacing.md,
  },
  agentBookings: {
    ...typography.caption,
    color: colors.textSecondary,
    marginRight: spacing.md,
  },
  agentTypeBadge: {
    paddingHorizontal: spacing.xs + 2,
    paddingVertical: spacing.xs / 2,
    borderRadius: radius.sm,
  },
  travelBadge: {
    backgroundColor: colors.success + '20',
  },
  transportBadge: {
    backgroundColor: colors.warning + '20',
  },
  agentTypeText: {
    fontSize: 10,
    fontWeight: '500',
    color: colors.text,
  },
});