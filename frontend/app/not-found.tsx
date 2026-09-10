import Link from "next/link";

export default function NotFound() {
  return (
    <div className="panel mx-auto max-w-lg p-8 text-center">
      <h1 className="text-2xl">Page not found</h1>
      <p className="mt-2 text-muted">That disease, protein, or route is not part of this research platform.</p>
      <Link href="/" className="mt-4 inline-block text-accent">
        Return home
      </Link>
    </div>
  );
}
