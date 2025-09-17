import React from 'react';
import { View, Image, Text, StyleSheet } from 'react-native';
import { colors, radius } from '../../constants/theme';

// Import avatar data
const agentAvatars = {
  avatar1: require('../../assets/agent_avatars/avatar1.jpg'),
  avatar2: require('../../assets/agent_avatars/avatar2.jpg'), 
  avatar3: require('../../assets/agent_avatars/avatar3.jpg'),
  avatar4: require('../../assets/agent_avatars/avatar4.jpg'),
  avatar5: require('../../assets/agent_avatars/avatar5.jpg'),
  avatar6: require('../../assets/agent_avatars/avatar6.jpg'),
  avatar7: require('../../assets/agent_avatars/avatar7.jpg'),
  avatar8: require('../../assets/agent_avatars/avatar8.jpg'),
};

interface AvatarProps {
  avatar_id?: string;
  name: string;
  size?: 'small' | 'medium' | 'large';
  style?: any;
}

export const Avatar: React.FC<AvatarProps> = ({
  avatar_id,
  name,
  size = 'medium',
  style,
}) => {
  const sizeMap = {
    small: 40,
    medium: 80,
    large: 120,
  };

  const avatarSize = sizeMap[size];
  const fontSize = Math.floor(avatarSize * 0.4);

  // Get avatar image source
  const getAvatarSource = () => {
    if (avatar_id && agentAvatars[avatar_id as keyof typeof agentAvatars]) {
      return agentAvatars[avatar_id as keyof typeof agentAvatars];
    }
    return null;
  };

  const avatarSource = getAvatarSource();

  const containerStyle = [
    styles.container,
    {
      width: avatarSize,
      height: avatarSize,
      borderRadius: avatarSize / 2,
    },
    style,
  ];

  if (avatarSource) {
    return (
      <Image
        source={avatarSource}
        style={[
          containerStyle,
          styles.image,
        ]}
        resizeMode="cover"
      />
    );
  }

  // Fallback to initial letter
  return (
    <View style={[containerStyle, styles.fallback]}>
      <Text style={[styles.fallbackText, { fontSize }]}>
        {name.charAt(0).toUpperCase()}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  image: {
    // Image styles are applied via containerStyle
  },
  fallback: {
    backgroundColor: colors.primaryLight,
  },
  fallbackText: {
    color: colors.primary,
    fontWeight: 'bold',
  },
});