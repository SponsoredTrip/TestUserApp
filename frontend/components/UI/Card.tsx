import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { components, colors, radius, spacing, shadows } from '../../constants/theme';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  shadow?: 'small' | 'medium' | 'large';
  padding?: number;
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  style, 
  shadow = 'medium',
  padding = spacing.md 
}) => {
  return (
    <View style={[
      styles.card,
      shadows[shadow],
      { padding },
      style
    ]}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    marginVertical: spacing.xs,
  },
});