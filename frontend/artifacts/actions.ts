export async function getSuggestions({
  documentId: _documentId,
}: {
  documentId: string;
}) {
  // Backend-driven suggestions are currently not implemented in this frontend.
  // Returning an empty list keeps the UI working without any local DB.
  return [];
}

