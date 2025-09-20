import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import { useState, useRef } from 'react';
import { Button, Text, ScrollView, StyleSheet, View, TouchableOpacity, Image } from 'react-native';
import * as MediaLibrary from 'expo-media-library';

export default function App() {
  const [facing, setFacing] = useState<CameraType>('back');
  const [permission, camRequestPermission] = useCameraPermissions();
  const [albums, setAlbums] = useState<any[] | null>(null);
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [permissionResponse, requestPermission] = MediaLibrary.usePermissions();
  const cameraRef = useRef<CameraView | null>(null);

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>We need your permission to show the camera</Text>
        <Button onPress={requestPermission} title="Grant permission" />
      </View>
    );
  }

  function toggleCameraFacing() {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  }

  async function takePicture() {
    if (cameraRef.current) {
      try {
        const photo = await cameraRef.current.takePictureAsync();
        setPhotoUri(photo.uri);

        // Save to gallery (optional)
        const perm = await MediaLibrary.requestPermissionsAsync();
        if (perm.granted) {
          await MediaLibrary.saveToLibraryAsync(photo.uri);
        }
      } catch (e) {
        console.warn('Failed to take picture', e);
      }
    }
  }

  return (
    <View style={styles.container}>
      <CameraView style={styles.camera} facing={facing} ref={cameraRef} />

      {/* Buttons anchored to bottom */}
      <View style={styles.buttonContainer}>
        <TouchableOpacity style={styles.button} onPress={toggleCameraFacing}>
          <Text style={styles.text}>Flip Camera</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.button} onPress={takePicture}>
          <Text style={styles.text}>Take Picture</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.getAlbumsButton]}
          onPress={async () => {
            try {
              const perm = await MediaLibrary.requestPermissionsAsync();
              if (!perm.granted) {
                alert('Media library permission is required to get albums.');
                return;
              }
              const a = await MediaLibrary.getAlbumsAsync();
              setAlbums(a);
            } catch (e) {
              console.warn('Failed to get albums', e);
            }
          }}
        >
          <Text style={styles.text}>Get Albums</Text>
        </TouchableOpacity>
      </View>

      {/* Preview of last photo */}
      {photoUri && (
        <View style={styles.previewContainer}>
          <Image source={{ uri: photoUri }} style={styles.preview} />
        </View>
      )}

      {/* Albums overlay */}
      {albums && (
        <View style={styles.albumsContainer} pointerEvents="box-none">
          <ScrollView style={styles.albumsList}>
            {albums.map((alb: any) => (
              <View key={alb.id} style={styles.albumRow}>
                <Text style={styles.albumText}>{alb.title}</Text>
              </View>
            ))}
          </ScrollView>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center' },
  message: { textAlign: 'center', paddingBottom: 10 },
  camera: { flex: 1 },
  buttonContainer: {
    position: 'absolute',
    bottom: 64,
    flexDirection: 'row',
    backgroundColor: 'transparent',
    width: '100%',
    paddingHorizontal: 16,
    justifyContent: 'space-around',
  },
  button: { alignItems: 'center' },
  text: { fontSize: 18, fontWeight: 'bold', color: 'white' },
  getAlbumsButton: { alignItems: 'center' },
  albumsContainer: {
    position: 'absolute',
    bottom: 140,
    left: 16,
    right: 16,
    maxHeight: 240,
  },
  albumsList: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    borderRadius: 8,
    padding: 8,
  },
  albumRow: {
    paddingVertical: 8,
    borderBottomColor: 'rgba(255,255,255,0.1)',
    borderBottomWidth: 1,
  },
  albumText: { color: 'white', fontSize: 16 },
  previewContainer: {
    position: 'absolute',
    top: 64,
    right: 16,
    borderWidth: 2,
    borderColor: 'white',
    borderRadius: 8,
    overflow: 'hidden',
  },
  preview: { width: 100, height: 150 },
});
