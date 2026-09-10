import type { Metadata } from "next";
import { ProteinExplorer } from "@/components/ProteinExplorer";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  return {
    title: `Gene ${id} — Disease–Protein Network Explorer`,
    description: `Network neighborhood and disease associations for Entrez Gene ${id}.`,
  };
}

export default async function ProteinPage({ params }: Props) {
  const { id } = await params;
  return <ProteinExplorer proteinId={id} />;
}
