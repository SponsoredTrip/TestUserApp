import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ViewStyle, TextStyle } from 'react-native';
import { colors, radius, spacing, shadows, typography } from '../../constants/theme';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  style,
  textStyle,
}) => {
  const getButtonStyle = () => {
    const baseStyle = [styles.button];
    
    // Size styles
    if (size === 'small') baseStyle.push(styles.small);
    else if (size === 'large') baseStyle.push(styles.large);
    else baseStyle.push(styles.medium);
    
    // Variant styles
    if (variant === 'primary') baseStyle.push(styles.primary);
    else if (variant === 'secondary') baseStyle.push(styles.secondary);
    else if (variant === 'outline') baseStyle.push(styles.outline);
    
    // Disabled style
    if (disabled) baseStyle.push(styles.disabled);
    
    return baseStyle;
  };

  const getTextStyle = () => {
    const baseStyle = [styles.text];
    
    if (variant === 'primary') baseStyle.push(styles.primaryText);
    else if (variant === 'secondary') baseStyle.push(styles.secondaryText);
    else if (variant === 'outline') baseStyle.push(styles.outlineText);
    
    if (disabled) baseStyle.push(styles.disabledText);
    
    return baseStyle;
  };

  return (
    <TouchableOpacity
      style={[...getButtonStyle(), style]}
      onPress={onPress}
      disabled={disabled}
      activeOpacity={0.8}
    >
      <Text style={[...getTextStyle(), textStyle]}>{title}</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.small,
  },
  
  // Size variants  
  small: {
    paddingVertical: spacing.xs + 2,
    paddingHorizontal: spacing.sm + 4,
    minHeight: 32,
  },
  medium: {
    paddingVertical: spacing.sm + 4,
    paddingHorizontal: spacing.md + 8,
    minHeight: 44,
  },
  large: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg + 8,
    minHeight: 52,
  },
  
  // Color variants
  primary: {
    backgroundColor: colors.primary,
  },
  secondary: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: colors.primary,
  },
  
  // Disabled state
  disabled: {
    backgroundColor: colors.textSecondary,
    opacity: 0.6,
  },
  
  // Text styles
  text: {
    ...typography.button,
    textAlign: 'center',
  },
  primaryText: {
    color: colors.textLight,
  },
  secondaryText: {
    color: colors.primary,
  },
  outlineText: {
    color: colors.primary,
  },
  disabledText: {
    color: colors.textLight,
  },
});