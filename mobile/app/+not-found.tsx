import { Link, Stack } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { useSensor } from "@/contexts/SensorContext";
import Colors from "@/constants/colors";

export default function NotFoundScreen() {
  const { isDarkMode } = useSensor();
  const colors = isDarkMode ? Colors.dark : Colors.light;

  return (
    <>
      <Stack.Screen options={{ title: "Not Found" }} />
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Text style={[styles.title, { color: colors.text }]}>Page not found</Text>
        <Text style={[styles.description, { color: colors.textSecondary }]}>
          The screen you&apos;re looking for doesn&apos;t exist.
        </Text>

        <Link href="/" style={[styles.link, { backgroundColor: colors.primary }]}>
          <Text style={styles.linkText}>Return to Dashboard</Text>
        </Link>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: "700" as const,
    marginBottom: 8,
  },
  description: {
    fontSize: 16,
    textAlign: "center",
    marginBottom: 32,
  },
  link: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  linkText: {
    fontSize: 16,
    fontWeight: "600" as const,
    color: "#FFFFFF",
  },
});
