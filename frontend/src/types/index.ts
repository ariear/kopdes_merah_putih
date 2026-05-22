export type Product = {
    id: number;
    name: string;
    price: number;
    description: string;
    image: string;
    available_amount: number;
};

export type CartItem = {
    product: Product;
    qty: number;
};
