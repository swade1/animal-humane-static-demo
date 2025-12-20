export async function fetchLengthOfStayDistribution() {
  const response = await fetch('/api/length-of-stay-distribution');
  if (!response.ok) throw new Error('Failed to fetch length of stay distribution');
  return response.json();
}