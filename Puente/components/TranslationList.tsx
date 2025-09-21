// components/TranslationList.tsx
import React, { useEffect } from "react";
import { View, Text, FlatList, StyleSheet, Alert } from "react-native";

interface TranslationItem {
  lang_detected: string;
  term: string;
  contextual_translation: string;
}

interface TranslationListProps {
  translations: TranslationItem[];
  originalText: string; // pass in the original Spanish text
}

export default function TranslationList({ translations, originalText }: TranslationListProps) {
    console.log("Scan Complete:", originalText);
  // Show alert automatically when translations change and are not empty
  useEffect(() => {
    if (translations.length > 0 && originalText) {
        console.log("Translation Complete:", originalText);
    }
  }, [translations, originalText]);

  if (!translations || translations.length === 0) {
    return null; // don't show anything if empty
  }

  return (
    <FlatList
      data={translations}
      keyExtractor={(_, index) => index.toString()}
      renderItem={({ item }) => (
        <View style={styles.item}>
          <Text style={styles.term}>{item.term}</Text>
          <Text style={styles.translation}>{item.contextual_translation}</Text>
          <Text style={styles.lang}>[{item.lang_detected}]</Text>
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  item: {
    padding: 12,
    borderBottomWidth: 1,
    borderColor: "#ddd",
  },
  term: {
    fontWeight: "bold",
    fontSize: 16,
  },
  translation: {
    fontSize: 14,
    color: "#333",
    marginTop: 2,
  },
  lang: {
    fontSize: 12,
    color: "#666",
    marginTop: 2,
  },
});
