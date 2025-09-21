// app/tabs/index.tsx
import React, { useState, useEffect } from "react";
import { View, Text, Button, StyleSheet, ScrollView } from "react-native";
import TranslationList from "../../components/TranslationList"; // adjust path if needed
import { uploadCamera } from "../../hooks/uploadCamera";

interface TranslationItem {
  lang_detected: string;
  term: string;
  contextual_translation: string;
}

interface TranslationResponse {
  original_text: string;
  translations: TranslationItem[];
}

export default function HomeScreen() {
  const { uploadCamera: upload } = { uploadCamera }; // using your hook/function
  const [translations, setTranslations] = useState<TranslationItem[]>([]);
  const [latestOriginalText, setLatestOriginalText] = useState("");

  // Log original text when new translation arrives
  useEffect(() => {
    if (translations.length > 0 && latestOriginalText) {
      console.log("Translation Complete:", latestOriginalText);
    }
  }, [translations, latestOriginalText]);

  const handleUpload = async () => {
    try {
      // Replace with actual photo URI from camera or picker
      const result: TranslationResponse = await upload("file:///path/to/photo.jpg");
      setTranslations(result.translations || []);
      setLatestOriginalText(result.original_text);
    } catch (err) {
      console.error("Upload failed:", err);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Welcome!</Text>
      <Button title="Upload Photo" onPress={handleUpload} />
      <View style={styles.listContainer}>
        <TranslationList translations={translations} originalText={latestOriginalText} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: "#fff",
    minHeight: "100%",
  },
  title: {
    fontSize: 28,
    fontWeight: "bold",
    marginBottom: 16,
    textAlign: "center",
  },
  listContainer: {
    marginTop: 20,
  },
});
