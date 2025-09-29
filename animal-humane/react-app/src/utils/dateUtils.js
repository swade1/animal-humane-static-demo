export function getLast8Days() {
  const result = [];
  const today = new Date();
  for (let i = 7; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    result.push(d.toISOString().slice(0, 10));
  }
  return result;
}

export function getLast8Weeks() {
  const result = [];
  const today = new Date();

  // Loop backwards 8 weeks, including the current week
  for (let i = 7; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i * 7); // subtract i weeks
    result.push(d.toISOString().slice(0, 10)); // format YYYY-MM-DD
  }
  return result;
}

export function getLast5Weeks() {
  const result = [];
  const today = new Date();

  // Loop backwards 5 weeks, including current week
  for (let i = 4; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i * 7); // subtract i weeks (7 days each)
    result.push(d.toISOString().slice(0, 10)); // 'YYYY-MM-DD'
  }

  return result;
}

