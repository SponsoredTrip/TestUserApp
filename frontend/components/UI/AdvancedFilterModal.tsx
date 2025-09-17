import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  Platform,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { colors, layout, spacing, typography, shadows, radius } from '../../constants/theme';
import { Card } from './Card';
import { Button } from './Button';

interface AdvancedFilterModalProps {
  visible: boolean;
  onClose: () => void;
  onApplyFilters: (filters: FilterOptions) => void;
  currentFilters: FilterOptions;
}

export interface FilterOptions {
  sortBy: string;
  dateFrom: Date | null;
  dateTo: Date | null;
  rating: string;
  sponsored: string;
}

export const AdvancedFilterModal: React.FC<AdvancedFilterModalProps> = ({
  visible,
  onClose,
  onApplyFilters,
  currentFilters,
}) => {
  const [filters, setFilters] = useState<FilterOptions>(currentFilters);
  const [showFromDatePicker, setShowFromDatePicker] = useState(false);
  const [showToDatePicker, setShowToDatePicker] = useState(false);

  const sortOptions = [
    { label: 'Relevance', value: 'relevance' },
    { label: 'Rating - High to Low', value: 'rating_desc' },
    { label: 'Rating - Low to High', value: 'rating_asc' },
    { label: 'Cost - Low to High', value: 'cost_asc' },
    { label: 'Cost - High to Low', value: 'cost_desc' },
  ];

  const ratingOptions = [
    { label: 'All Ratings', value: 'all' },
    { label: 'Rated 3.0★+', value: '3+' },
    { label: 'Rated 4.0★+', value: '4+' },
  ];

  const sponsoredOptions = [
    { label: 'All Offers', value: 'all' },
    { label: 'Up to 30% Off', value: '30' },
    { label: 'More than 50% Off', value: '50' },
  ];

  const handleApply = () => {
    onApplyFilters(filters);
    onClose();
  };

  const handleReset = () => {
    const resetFilters: FilterOptions = {
      sortBy: 'relevance',
      dateFrom: null,
      dateTo: null,
      rating: 'all',
      sponsored: 'all',
    };
    setFilters(resetFilters);
  };

  const formatDate = (date: Date | null) => {
    if (!date) return 'Select Date';
    return date.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const renderOption = (
    title: string,
    options: { label: string; value: string }[],
    currentValue: string,
    onSelect: (value: string) => void
  ) => (
    <View style={styles.optionSection}>
      <Text style={styles.optionTitle}>{title}</Text>
      <View style={styles.optionContainer}>
        {options.map((option) => (
          <TouchableOpacity
            key={option.value}
            style={[
              styles.optionChip,
              currentValue === option.value && styles.optionChipActive,
            ]}
            onPress={() => onSelect(option.value)}
          >
            <Text
              style={[
                styles.optionChipText,
                currentValue === option.value && styles.optionChipTextActive,
              ]}
            >
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Advanced Filters</Text>
          <TouchableOpacity onPress={handleReset} style={styles.resetButton}>
            <Text style={styles.resetButtonText}>Reset</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Sort By Section */}
          {renderOption(
            'Sort By',
            sortOptions,
            filters.sortBy,
            (value) => setFilters({ ...filters, sortBy: value })
          )}

          {/* Time/Schedule Section */}
          <View style={styles.optionSection}>
            <Text style={styles.optionTitle}>Schedule</Text>
            <View style={styles.dateContainer}>
              <View style={styles.datePickerContainer}>
                <Text style={styles.dateLabel}>From Date</Text>
                <TouchableOpacity
                  style={styles.dateButton}
                  onPress={() => setShowFromDatePicker(true)}
                >
                  <Text style={styles.dateButtonText}>
                    {formatDate(filters.dateFrom)}
                  </Text>
                </TouchableOpacity>
              </View>
              
              <View style={styles.datePickerContainer}>
                <Text style={styles.dateLabel}>To Date</Text>
                <TouchableOpacity
                  style={styles.dateButton}
                  onPress={() => setShowToDatePicker(true)}
                >
                  <Text style={styles.dateButtonText}>
                    {formatDate(filters.dateTo)}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>

          {/* Rating Section */}
          {renderOption(
            'Rating',
            ratingOptions,
            filters.rating,
            (value) => setFilters({ ...filters, rating: value })
          )}

          {/* Sponsored Section */}
          {renderOption(
            'Sponsored Offers',
            sponsoredOptions,
            filters.sponsored,
            (value) => setFilters({ ...filters, sponsored: value })
          )}
        </ScrollView>

        {/* Footer */}
        <View style={styles.footer}>
          <Button
            title="Apply Filters"
            onPress={handleApply}
            style={styles.applyButton}
          />
        </View>

        {/* Date Pickers - Outside ScrollView */}
        {showFromDatePicker && (
          <DateTimePicker
            value={filters.dateFrom || new Date()}
            mode="date"
            display={Platform.OS === 'ios' ? 'spinner' : 'default'}
            onChange={(event, selectedDate) => {
              setShowFromDatePicker(false);
              if (selectedDate) {
                setFilters({ ...filters, dateFrom: selectedDate });
              }
            }}
          />
        )}

        {showToDatePicker && (
          <DateTimePicker
            value={filters.dateTo || new Date()}
            mode="date"
            display={Platform.OS === 'ios' ? 'spinner' : 'default'}
            onChange={(event, selectedDate) => {
              setShowToDatePicker(false);
              if (selectedDate) {
                setFilters({ ...filters, dateTo: selectedDate });
              }
            }}
          />
        )}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.primaryLight,
    ...shadows.small,
  },
  closeButton: {
    padding: spacing.xs,
  },
  closeButtonText: {
    fontSize: 18,
    color: colors.textSecondary,
  },
  headerTitle: {
    ...typography.h3,
    color: colors.primary,
  },
  resetButton: {
    padding: spacing.xs,
  },
  resetButtonText: {
    ...typography.body2,
    color: colors.primary,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    paddingHorizontal: spacing.md,
  },
  optionSection: {
    marginVertical: spacing.md,
  },
  optionTitle: {
    ...typography.h4,
    marginBottom: spacing.sm,
  },
  optionContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  optionChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    backgroundColor: colors.surfaceLight,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: colors.primaryLight,
    ...shadows.small,
  },
  optionChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  optionChipText: {
    ...typography.body2,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  optionChipTextActive: {
    color: colors.textLight,
  },
  dateContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: spacing.sm,
  },
  datePickerContainer: {
    flex: 1,
  },
  dateLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
    textTransform: 'uppercase',
  },
  dateButton: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primaryLight,
    borderRadius: radius.md,
    paddingVertical: spacing.sm + 2,
    paddingHorizontal: spacing.md,
    ...shadows.small,
  },
  dateButtonText: {
    ...typography.body2,
    color: colors.text,
    textAlign: 'center',
  },
  footer: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.primaryLight,
  },
  applyButton: {
    marginTop: 0,
  },
});