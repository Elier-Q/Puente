// app/tabs/explore.tsx
import React, { useState, useRef } from "react";
import { View, Text, TouchableOpacity, StyleSheet, Image, Button } from "react-native";
import { CameraView, CameraType, useCameraPermissions } from "expo-camera";
import * as ImagePicker from "expo-image-picker";
import { uploadCamera } from "../../hooks/uploadCamera";

export default function ExploreScreen() {
  const [facing] = useState<CameraType>("back"); // No flip button, so facing is fixed
  const [permission, requestPermission] = useCameraPermissions();
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const cameraRef = useRef<CameraView | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!permission) return <View />;

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>Camera permission required</Text>
        <Button onPress={requestPermission} title="Grant permission" />
      </View>
    );
  }

  const takePicture = async () => {
    if (!cameraRef.current) return;
    try {
      const photo = await cameraRef.current.takePictureAsync();
      setPhotoUri(photo.uri);
      setLoading(true);
      setError(null);
      await uploadCamera(photo.uri);
    } catch (err: any) {
      setError(err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const pickImageFromAlbum = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 1,
      });

      if (!result.canceled) {
        const uri = result.assets[0].uri;
        setPhotoUri(uri);
        setLoading(true);
        setError(null);
        await uploadCamera(uri);
      }
    } catch (err: any) {
      setError(err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <CameraView style={styles.camera} facing={facing} ref={cameraRef} />

      <View style={styles.buttonContainer}>
        <TouchableOpacity style={styles.button} onPress={takePicture}>
          <Text style={styles.buttonText}>Snap</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.button} onPress={pickImageFromAlbum}>
          <Text style={styles.buttonText}>Album</Text>
        </TouchableOpacity>
      </View>

      {photoUri && (
        <View style={styles.previewContainer}>
          <Image source={{ uri: photoUri }} style={styles.preview} />
        </View>
      )}

      {loading && <Text style={styles.message}>Uploading...</Text>}
      {error && <Text style={[styles.message, { color: "red" }]}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  camera: { flex: 1 },
  buttonContainer: {
    position: "absolute",
    bottom: 64,
    flexDirection: "row",
    justifyContent: "space-around",
    width: "100%",
    paddingHorizontal: 16,
  },
  button: { alignItems: "center" },
  buttonText: { color: "white", fontSize: 18, fontWeight: "bold" },
  previewContainer: {
    position: "absolute",
    top: 64,
    right: 16,
    borderWidth: 2,
    borderColor: "white",
    borderRadius: 8,
    overflow: "hidden",
  },
  preview: { width: 100, height: 150 },
  message: { textAlign: "center", padding: 10, color: "white" },
});
