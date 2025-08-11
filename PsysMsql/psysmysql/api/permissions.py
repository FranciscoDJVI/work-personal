"""
Custom permissions for PsysMsql API

This module defines custom permission classes to control access to API endpoints
based on user roles and ownership.
"""

from rest_framework import permissions
from django.contrib.auth.models import Group


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to create/edit/delete.
    Read-only permissions are allowed to any authenticated user.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions are only allowed to admin users
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or self.is_admin_user(request.user))
        )
    
    def is_admin_user(self, user):
        """Check if user is in admin group"""
        try:
            admin_group = Group.objects.get(name='Admin')
            return admin_group in user.groups.all()
        except Group.DoesNotExist:
            return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to access it.
    """

    def has_permission(self, request, view):
        # Permission is allowed to any authenticated user for list/create actions
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is admin
        if request.user.is_staff or self.is_admin_user(request.user):
            return True
        
        # Check ownership based on object type
        if hasattr(obj, 'user'):
            # For objects with user field (like Sell)
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            # For objects with created_by field
            return obj.created_by == request.user
        elif obj == request.user:
            # For User model itself
            return True
        
        # Default: deny access
        return False
    
    def is_admin_user(self, user):
        """Check if user is in admin group"""
        try:
            admin_group = Group.objects.get(name='Admin')
            return admin_group in user.groups.all()
        except Group.DoesNotExist:
            return False


class IsSellerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow sellers and admins to access sales-related endpoints.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admins have full access
        if request.user.is_staff or self.is_admin_user(request.user):
            return True
        
        # Sellers have access to sales operations
        return self.is_seller_user(request.user)

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admins have full access
        if request.user.is_staff or self.is_admin_user(request.user):
            return True
        
        # Sellers can access their own sales
        if self.is_seller_user(request.user):
            if hasattr(obj, 'user') and obj.user == request.user:
                return True
        
        return False
    
    def is_admin_user(self, user):
        """Check if user is in admin group"""
        try:
            admin_group = Group.objects.get(name='Admin')
            return admin_group in user.groups.all()
        except Group.DoesNotExist:
            return False
    
    def is_seller_user(self, user):
        """Check if user is in seller group"""
        try:
            seller_group = Group.objects.get(name='Seller')
            return seller_group in user.groups.all()
        except Group.DoesNotExist:
            return False


class IsAdminUser(permissions.BasePermission):
    """
    Permission class to allow access only to admin users.
    """

    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or self.is_admin_user(request.user))
        )
    
    def is_admin_user(self, user):
        """Check if user is in admin group"""
        try:
            admin_group = Group.objects.get(name='Admin')
            return admin_group in user.groups.all()
        except Group.DoesNotExist:
            return False


class ReadOnlyPermission(permissions.BasePermission):
    """
    Permission class to allow only read access.
    """

    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.method in permissions.SAFE_METHODS
        )
