export type Nullable<T> = T | null | undefined;

export type Stat = {
	label: string;
	value: string | number;
	help?: string;
};
