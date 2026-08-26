package com.shopizer.guava.compat;

import com.google.common.collect.ImmutableList; // New package location
import com.google.common.collect.Lists; // New package location
import com.google.common.base.Preconditions; // New utility functions

// TODO: Manually review usages of deprecated classes and methods, such as "Suppliers" which may need replacements.

public class GuavaCompat {

    /**
     * Wrapper for ImmutableList.of() to maintain backward compatibility.
     */
    public static <E> ImmutableList<E> of(E... elements) {
        return ImmutableList.copyOf(elements); // Replacing old API with new equivalent
    }

    /**
     * Wrapper for Lists.newArrayList() to maintain backward compatibility.
     */
    public static <E> java.util.List<E> newArrayList(E... elements) {
        return Lists.newArrayList(elements); // Replacing old API with new equivalent
    }

    /**
     * Compatibility method to demonstrate the move from old utility classes to new replacements.
     */
    public static <T> T checkNotNull(T reference) {
        return Preconditions.checkNotNull(reference); // Utilizing new Preconditions for null checks
    }

    // Example of how to handle deprecated methods
    // TODO: Replace all usages of com.google.common.base.Suppliers.memoize
    // using contexts that may require manual intervention for exact logic preservation.

    // Add more wrappers as needed for other commonly used methods

}