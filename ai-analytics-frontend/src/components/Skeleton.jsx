export default function Skeleton({ width = "100%", height = "20px", count = 1 }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          style={{
            width,
            height,
            background: "linear-gradient(90deg, var(--bg3) 25%, var(--border) 50%, var(--bg3) 75%)",
            backgroundSize: "200% 100%",
            animation: "loading 1.5s infinite",
            borderRadius: 8,
            marginBottom: i < count - 1 ? 12 : 0,
          }}
        />
      ))}
      <style>{`
        @keyframes loading {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </>
  );
}