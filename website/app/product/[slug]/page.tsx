import { notFound } from "next/navigation";
import { getProduct, products } from "@/lib/products";
import { ProductPageV3 } from "@/components/v3/product-page-v3";
import { WorkforcePageV10 } from "@/components/v3/workforce-page-v10";

export function generateStaticParams() {
  return products.map(product => ({ slug: product.slug }));
}

export default async function ProductPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const product = getProduct(slug);
  if (!product) notFound();
  if (slug === "workforce") return <WorkforcePageV10 />;
  return <ProductPageV3 product={product} />;
}
