import Link from "next/link";

export default function NotFound() {
  return (
    <div className="panel mx-auto max-w-lg p-8 text-center">
      <h1 className="page-title text-[2rem]">Page not found</h1>
      <p className="mt-2 text-muted">That disease, protein, or route is not part of this research platform.</p>
      <div className="mt-4 flex justify-center gap-4 text-sm">
        <Link href="/" className="text-accent">
          Home
        </Link>
        <Link href="/diseases" className="text-accent">
          Diseases
        </Link>
      </div>
    </div>
  );
}
